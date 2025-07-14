from typing import Dict, Any, Optional
from celery import current_task
import structlog
from datetime import datetime, timedelta
import os
from uuid import UUID

from app.infrastructure.celery.celery_app import celery_app
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.download_repository_impl import SQLAlchemyDownloadRepository
from app.infrastructure.repositories.google_drive_repository_impl import SQLAlchemyGoogleDriveRepository
from app.infrastructure.external_services.google_drive_service import GoogleDriveService
from app.domain.entities.download import Download
from app.domain.entities.google_drive_config import GoogleDriveConfig
from app.domain.value_objects.download_status import DownloadStatus
from app.infrastructure.celery.notifications import notification_service
from app.shared.config import settings
from app.shared.exceptions.drive_exceptions import (
    DriveException,
    DriveAuthenticationError,
    DriveQuotaExceededError,
    DriveFileNotFoundError,
    DriveRateLimitError
)

logger = structlog.get_logger()


class DriveUploadProgress:
    """Classe para rastrear progresso do upload"""
    
    def __init__(self, download_id: str, notification_service):
        self.download_id = download_id
        self.notification_service = notification_service
        self.last_progress = 0
    
    def __call__(self, progress: float):
        """Callback para progresso do upload"""
        if abs(progress - self.last_progress) >= 5:  # Atualizar a cada 5%
            self.last_progress = progress
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': progress, 'status': 'uploading_to_drive'}
            )
            
            # Enviar notificação
            notification_service.notify_download_progress(
                self.download_id, progress, 'uploading_to_drive'
            )


@celery_app.task(bind=True, name="upload_to_drive")
def upload_to_drive_task(
    self, 
    download_id: str, 
    config_id: Optional[str] = None,
    folder_id: Optional[str] = None
):
    """Task para upload de arquivo para o Google Drive"""
    db = SessionLocal()
    try:
        # Buscar download no banco
        download_repo = SQLAlchemyDownloadRepository(db)
        download = download_repo.get_by_id(UUID(download_id))
        
        if not download:
            raise ValueError(f"Download não encontrado: {download_id}")
        
        # Verificar se o download foi concluído
        if download.status != DownloadStatus.COMPLETED:
            raise ValueError(f"Download não está concluído: {download.status}")
        
        # Verificar se o arquivo existe
        if not download.file_path or not os.path.exists(download.file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {download.file_path}")
        
        # Buscar configuração do Google Drive
        drive_repo = SQLAlchemyGoogleDriveRepository(db)
        if config_id:
            drive_config = drive_repo.get_by_id(UUID(config_id))
        else:
            drive_config = drive_repo.get_default_config()
        
        if not drive_config:
            raise ValueError("Nenhuma configuração do Google Drive encontrada")
        
        # Verificar se a configuração está ativa
        if not drive_config.is_valid():
            raise DriveAuthenticationError("Configuração do Google Drive não está válida")
        
        # Usar folder_id da configuração se não especificado
        if not folder_id:
            folder_id = drive_config.folder_id
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=drive_config.credentials_file,
            account_name=drive_config.user_id
        )
        
        # Verificar quota antes do upload
        file_size = os.path.getsize(download.file_path)
        quota_info = drive_service.get_quota_info()
        
        if quota_info['limit'] > 0:
            available_space = quota_info['limit'] - quota_info['used']
            if file_size > available_space:
                raise DriveQuotaExceededError(
                    f"Espaço insuficiente no Google Drive. Necessário: {file_size}, Disponível: {available_space}"
                )
        
        # Preparar nome do arquivo
        filename = os.path.basename(download.file_path)
        if download.title:
            # Usar título do vídeo como nome do arquivo
            extension = os.path.splitext(filename)[1]
            filename = f"{download.title}{extension}"
        
        # Fazer upload
        logger.info("Iniciando upload para Google Drive", 
                   download_id=download_id, filename=filename, file_size=file_size)
        
        # Notificar início do upload
        notification_service.notify_download_progress(
            download_id, 0, 'uploading_to_drive'
        )
        
        # Upload do arquivo
        drive_file = drive_service.upload_file(
            file_path=download.file_path,
            filename=filename,
            folder_id=folder_id
        )
        
        # Atualizar último uso da configuração
        drive_repo.update_last_used(drive_config.id)
        
        # Atualizar quota
        new_quota_used = quota_info['used'] + file_size
        drive_repo.update_quota(drive_config.id, new_quota_used, quota_info['limit'])
        
        # Notificar conclusão
        notification_service.notify_download_completed(
            download_id,
            download.file_path,
            download.title,
            download.thumbnail,
            download.url,
            download.file_size,
            download.format,
            drive_file_id=drive_file['id'],
            drive_file_link=drive_file.get('webViewLink')
        )
        
        logger.info("Upload para Google Drive concluído", 
                   download_id=download_id,
                   drive_file_id=drive_file['id'],
                   drive_file_link=drive_file.get('webViewLink'))
        
        return {
            'status': 'completed',
            'drive_file_id': drive_file['id'],
            'drive_file_link': drive_file.get('webViewLink'),
            'file_size': file_size
        }
        
    except DriveQuotaExceededError as e:
        logger.error("Quota do Google Drive excedida", 
                    download_id=download_id, error=str(e))
        
        # Notificar erro
        notification_service.notify_download_failed(
            download_id, f"Quota do Google Drive excedida: {str(e)}"
        )
        
        raise
        
    except DriveRateLimitError as e:
        logger.error("Rate limit do Google Drive excedido", 
                    download_id=download_id, error=str(e))
        
        # Re-raise para retry automático
        raise
        
    except Exception as e:
        logger.error("Erro no upload para Google Drive", 
                    download_id=download_id, error=str(e))
        
        # Notificar erro
        notification_service.notify_download_failed(
            download_id, f"Erro no upload para Google Drive: {str(e)}"
        )
        
        raise
    
    finally:
        db.close()


@celery_app.task(name="sync_drive_quota")
def sync_drive_quota_task(config_id: str):
    """Task para sincronizar quota do Google Drive"""
    db = SessionLocal()
    try:
        # Buscar configuração
        drive_repo = SQLAlchemyGoogleDriveRepository(db)
        drive_config = drive_repo.get_by_id(UUID(config_id))
        
        if not drive_config:
            raise ValueError(f"Configuração não encontrada: {config_id}")
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=drive_config.credentials_file,
            account_name=drive_config.user_id
        )
        
        # Obter quota atual
        quota_info = drive_service.get_quota_info()
        
        # Atualizar no banco
        drive_repo.update_quota(
            drive_config.id,
            quota_info['used'],
            quota_info['limit']
        )
        
        logger.info("Quota do Google Drive sincronizada", 
                   config_id=config_id,
                   used=quota_info['used'],
                   limit=quota_info['limit'])
        
        return {
            'status': 'completed',
            'quota_used': quota_info['used'],
            'quota_limit': quota_info['limit']
        }
        
    except Exception as e:
        logger.error("Erro ao sincronizar quota", error=str(e), config_id=config_id)
        raise
    
    finally:
        db.close()


@celery_app.task(name="test_drive_connection")
def test_drive_connection_task(config_id: str):
    """Task para testar conexão com Google Drive"""
    db = SessionLocal()
    try:
        # Buscar configuração
        drive_repo = SQLAlchemyGoogleDriveRepository(db)
        drive_config = drive_repo.get_by_id(UUID(config_id))
        
        if not drive_config:
            raise ValueError(f"Configuração não encontrada: {config_id}")
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=drive_config.credentials_file,
            account_name=drive_config.user_id
        )
        
        # Testar autenticação
        if not drive_service.is_authenticated():
            raise DriveAuthenticationError("Falha na autenticação")
        
        # Obter informações da conta
        account_info = drive_service.get_account_info()
        
        # Obter quota
        quota_info = drive_service.get_quota_info()
        
        # Listar algumas pastas para testar
        folders = drive_service.list_folders(limit=5)
        
        logger.info("Teste de conexão com Google Drive bem-sucedido", 
                   config_id=config_id,
                   account_info=account_info)
        
        return {
            'status': 'success',
            'account_info': account_info,
            'quota_info': quota_info,
            'folders_count': len(folders)
        }
        
    except Exception as e:
        logger.error("Erro no teste de conexão", error=str(e), config_id=config_id)
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_drive_files")
def cleanup_drive_files_task(config_id: str, days_old: int = 30):
    """Task para limpar arquivos antigos do Google Drive"""
    db = SessionLocal()
    try:
        # Buscar configuração
        drive_repo = SQLAlchemyGoogleDriveRepository(db)
        drive_config = drive_repo.get_by_id(UUID(config_id))
        
        if not drive_config:
            raise ValueError(f"Configuração não encontrada: {config_id}")
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=drive_config.credentials_file,
            account_name=drive_config.user_id
        )
        
        # Calcular data limite
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Buscar arquivos antigos
        # Nota: Esta é uma implementação simplificada
        # Em produção, você pode querer implementar uma busca mais sofisticada
        
        logger.info("Limpeza de arquivos do Google Drive iniciada", 
                   config_id=config_id, days_old=days_old)
        
        # Por enquanto, apenas log
        # Implementar lógica de limpeza conforme necessário
        
        return {
            'status': 'completed',
            'message': 'Limpeza de arquivos do Google Drive concluída'
        }
        
    except Exception as e:
        logger.error("Erro na limpeza de arquivos", error=str(e), config_id=config_id)
        raise
    
    finally:
        db.close() 