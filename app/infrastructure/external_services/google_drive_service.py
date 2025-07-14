from typing import Optional, List, Dict, Any, BinaryIO
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import os
import json
import structlog
from datetime import datetime, timedelta
import io

from app.shared.config import settings
from app.shared.exceptions.drive_exceptions import (
    DriveException,
    DriveAuthenticationError,
    DriveQuotaExceededError,
    DriveFileNotFoundError,
    DriveRateLimitError
)

logger = structlog.get_logger()

# Escopos necessários para Google Drive API
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]


class GoogleDriveService:
    """Serviço para integração com Google Drive API"""
    
    def __init__(self, credentials_file: str, account_name: str = "default"):
        self.credentials_file = credentials_file
        self.account_name = account_name
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Autentica com Google Drive API"""
        try:
            # Verificar se o arquivo de credenciais existe
            if not os.path.exists(self.credentials_file):
                raise DriveAuthenticationError(
                    f"Arquivo de credenciais não encontrado: {self.credentials_file}"
                )
            
            # Carregar credenciais do arquivo
            with open(self.credentials_file, 'r') as f:
                credentials_data = json.load(f)
            
            # Criar credenciais
            self.credentials = Credentials.from_authorized_user_info(
                credentials_data, SCOPES
            )
            
            # Verificar se as credenciais precisam ser renovadas
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            
            # Construir serviço
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            logger.info("Autenticação com Google Drive realizada com sucesso", 
                       account_name=self.account_name)
            
        except Exception as e:
            logger.error("Erro na autenticação com Google Drive", 
                        error=str(e), account_name=self.account_name)
            raise DriveAuthenticationError(f"Falha na autenticação: {str(e)}")
    
    def get_quota_info(self) -> Dict[str, Any]:
        """Obtém informações de quota do Google Drive"""
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            quota = about.get('storageQuota', {})
            
            return {
                'used': int(quota.get('usage', 0)),
                'limit': int(quota.get('limit', 0)),
                'usage_in_drive': int(quota.get('usageInDrive', 0)),
                'usage_in_drive_trash': int(quota.get('usageInDriveTrash', 0))
            }
            
        except HttpError as e:
            if e.resp.status == 403:
                raise DriveQuotaExceededError("Acesso negado para quota")
            raise DriveException(f"Erro ao obter quota: {str(e)}")
        except Exception as e:
            logger.error("Erro ao obter quota do Google Drive", error=str(e))
            raise DriveException(f"Erro ao obter quota: {str(e)}")
    
    def list_folders(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista pastas no Google Drive"""
        try:
            query = "mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                fields="files(id,name,createdTime,modifiedTime,parents)",
                orderBy="name"
            ).execute()
            
            folders = results.get('files', [])
            logger.info("Pastas listadas com sucesso", count=len(folders))
            
            return folders
            
        except HttpError as e:
            if e.resp.status == 429:
                raise DriveRateLimitError("Rate limit excedido")
            raise DriveException(f"Erro ao listar pastas: {str(e)}")
        except Exception as e:
            logger.error("Erro ao listar pastas", error=str(e))
            raise DriveException(f"Erro ao listar pastas: {str(e)}")
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Cria uma nova pasta no Google Drive"""
        try:
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields="id,name,createdTime,parents"
            ).execute()
            
            logger.info("Pasta criada com sucesso", 
                       folder_name=name, folder_id=folder['id'])
            
            return folder
            
        except HttpError as e:
            if e.resp.status == 429:
                raise DriveRateLimitError("Rate limit excedido")
            raise DriveException(f"Erro ao criar pasta: {str(e)}")
        except Exception as e:
            logger.error("Erro ao criar pasta", error=str(e))
            raise DriveException(f"Erro ao criar pasta: {str(e)}")
    
    def upload_file(
        self, 
        file_path: str, 
        filename: Optional[str] = None,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Faz upload de um arquivo para o Google Drive"""
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(file_path):
                raise DriveFileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Usar nome do arquivo se não especificado
            if not filename:
                filename = os.path.basename(file_path)
            
            # Detectar MIME type se não especificado
            if not mime_type:
                mime_type = self._get_mime_type(file_path)
            
            # Verificar quota antes do upload
            file_size = os.path.getsize(file_path)
            quota_info = self.get_quota_info()
            
            if quota_info['limit'] > 0:
                available_space = quota_info['limit'] - quota_info['used']
                if file_size > available_space:
                    raise DriveQuotaExceededError(
                        f"Espaço insuficiente. Necessário: {file_size}, Disponível: {available_space}"
                    )
            
            # Preparar metadados do arquivo
            file_metadata = {
                'name': filename,
                'mimeType': mime_type
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Criar media upload
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True,
                chunksize=1024*1024  # 1MB chunks
            )
            
            # Fazer upload
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id,name,size,createdTime,parents,webViewLink,webContentLink"
            ).execute()
            
            logger.info("Arquivo enviado com sucesso", 
                       filename=filename, file_id=file['id'], size=file_size)
            
            return file
            
        except HttpError as e:
            if e.resp.status == 403:
                raise DriveQuotaExceededError("Acesso negado ou quota excedida")
            elif e.resp.status == 429:
                raise DriveRateLimitError("Rate limit excedido")
            raise DriveException(f"Erro no upload: {str(e)}")
        except Exception as e:
            logger.error("Erro no upload do arquivo", error=str(e), file_path=file_path)
            raise DriveException(f"Erro no upload: {str(e)}")
    
    def upload_from_memory(
        self,
        file_data: bytes,
        filename: str,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Faz upload de dados em memória para o Google Drive"""
        try:
            # Detectar MIME type se não especificado
            if not mime_type:
                mime_type = self._get_mime_type_from_extension(filename)
            
            # Verificar quota
            file_size = len(file_data)
            quota_info = self.get_quota_info()
            
            if quota_info['limit'] > 0:
                available_space = quota_info['limit'] - quota_info['used']
                if file_size > available_space:
                    raise DriveQuotaExceededError(
                        f"Espaço insuficiente. Necessário: {file_size}, Disponível: {available_space}"
                    )
            
            # Preparar metadados
            file_metadata = {
                'name': filename,
                'mimeType': mime_type
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Criar media upload
            media = MediaIoBaseUpload(
                io.BytesIO(file_data),
                mimetype=mime_type,
                resumable=True,
                chunksize=1024*1024
            )
            
            # Fazer upload
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id,name,size,createdTime,parents,webViewLink,webContentLink"
            ).execute()
            
            logger.info("Arquivo enviado da memória com sucesso", 
                       filename=filename, file_id=file['id'], size=file_size)
            
            return file
            
        except HttpError as e:
            if e.resp.status == 403:
                raise DriveQuotaExceededError("Acesso negado ou quota excedida")
            elif e.resp.status == 429:
                raise DriveRateLimitError("Rate limit excedido")
            raise DriveException(f"Erro no upload da memória: {str(e)}")
        except Exception as e:
            logger.error("Erro no upload da memória", error=str(e), filename=filename)
            raise DriveException(f"Erro no upload da memória: {str(e)}")
    
    def delete_file(self, file_id: str) -> bool:
        """Deleta um arquivo do Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info("Arquivo deletado com sucesso", file_id=file_id)
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                raise DriveFileNotFoundError(f"Arquivo não encontrado: {file_id}")
            elif e.resp.status == 429:
                raise DriveRateLimitError("Rate limit excedido")
            raise DriveException(f"Erro ao deletar arquivo: {str(e)}")
        except Exception as e:
            logger.error("Erro ao deletar arquivo", error=str(e), file_id=file_id)
            raise DriveException(f"Erro ao deletar arquivo: {str(e)}")
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Obtém informações de um arquivo"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id,name,size,mimeType,createdTime,modifiedTime,parents,webViewLink,webContentLink"
            ).execute()
            
            return file
            
        except HttpError as e:
            if e.resp.status == 404:
                raise DriveFileNotFoundError(f"Arquivo não encontrado: {file_id}")
            raise DriveException(f"Erro ao obter informações do arquivo: {str(e)}")
        except Exception as e:
            logger.error("Erro ao obter informações do arquivo", error=str(e), file_id=file_id)
            raise DriveException(f"Erro ao obter informações do arquivo: {str(e)}")
    
    def _get_mime_type(self, file_path: str) -> str:
        """Detecta o MIME type de um arquivo"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def _get_mime_type_from_extension(self, filename: str) -> str:
        """Detecta o MIME type baseado na extensão do arquivo"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def is_authenticated(self) -> bool:
        """Verifica se está autenticado"""
        return self.service is not None and self.credentials is not None
    
    def get_account_info(self) -> Dict[str, Any]:
        """Obtém informações da conta"""
        try:
            about = self.service.about().get(fields="user").execute()
            user = about.get('user', {})
            
            return {
                'email': user.get('emailAddress'),
                'name': user.get('displayName'),
                'account_name': self.account_name
            }
            
        except Exception as e:
            logger.error("Erro ao obter informações da conta", error=str(e))
            return {'account_name': self.account_name} 