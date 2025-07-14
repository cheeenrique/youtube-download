from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import secrets
import structlog
import os
from uuid import UUID
import json

from app.shared.config import settings
from app.domain.entities.temporary_file import TemporaryFile
from app.domain.repositories.temporary_file_repository import TemporaryFileRepository
from app.shared.exceptions.download_exceptions import (
    TemporaryFileExpiredError,
    TemporaryFileNotFoundError,
    TemporaryFileAccessDeniedError
)

logger = structlog.get_logger()


class TemporaryURLService:
    """Serviço para geração e gerenciamento de links temporários"""
    
    def __init__(self, temp_file_repo: TemporaryFileRepository):
        self.temp_file_repo = temp_file_repo
        self.base_url = settings.base_url if hasattr(settings, 'base_url') else "http://localhost:8000"
    
    def generate_temporary_url(
        self,
        download_id: UUID,
        file_path: str,
        expiration_hours: int = 1,
        max_accesses: Optional[int] = None,
        custom_filename: Optional[str] = None
    ) -> TemporaryFile:
        """Gera um link temporário para um arquivo"""
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Gerar token único
            token = self._generate_token()
            
            # Calcular hash do arquivo
            file_hash = self._calculate_file_hash(file_path)
            
            # Definir expiração
            expiration_time = datetime.utcnow() + timedelta(hours=expiration_hours)
            
            # Criar entidade TemporaryFile
            temp_file = TemporaryFile(
                download_id=download_id,
                file_path=file_path,
                expiration_time=expiration_time,
                access_count=0,
                temporary_url=f"{self.base_url}/api/v1/downloads/{download_id}/temp/{token}",
                file_hash=file_hash,
                max_accesses=max_accesses,
                custom_filename=custom_filename
            )
            
            # Salvar no repositório
            temp_file = self.temp_file_repo.create(temp_file)
            
            logger.info("Link temporário gerado", 
                       download_id=str(download_id),
                       token=token,
                       expiration_time=expiration_time.isoformat())
            
            return temp_file
            
        except Exception as e:
            logger.error("Erro ao gerar link temporário", 
                        error=str(e), download_id=str(download_id))
            raise
    
    def validate_temporary_url(self, download_id: UUID, token: str) -> TemporaryFile:
        """Valida um link temporário e retorna os dados do arquivo"""
        try:
            # Buscar arquivo temporário
            temp_file = self.temp_file_repo.get_by_download_and_token(download_id, token)
            
            if not temp_file:
                raise TemporaryFileNotFoundError("Link temporário não encontrado")
            
            # Verificar se expirou
            if datetime.utcnow() > temp_file.expiration_time:
                raise TemporaryFileExpiredError("Link temporário expirado")
            
            # Verificar limite de acessos
            if temp_file.max_accesses and temp_file.access_count >= temp_file.max_accesses:
                raise TemporaryFileAccessDeniedError("Limite de acessos excedido")
            
            # Verificar se o arquivo ainda existe
            if not os.path.exists(temp_file.file_path):
                raise TemporaryFileNotFoundError("Arquivo não encontrado no servidor")
            
            # Incrementar contador de acessos
            temp_file.access_count += 1
            self.temp_file_repo.update(temp_file)
            
            # Log do acesso
            logger.info("Acesso a link temporário", 
                       download_id=str(download_id),
                       token=token,
                       access_count=temp_file.access_count)
            
            return temp_file
            
        except (TemporaryFileExpiredError, TemporaryFileNotFoundError, TemporaryFileAccessDeniedError):
            raise
        except Exception as e:
            logger.error("Erro ao validar link temporário", 
                        error=str(e), download_id=str(download_id), token=token)
            raise
    
    def revoke_temporary_url(self, download_id: UUID, token: str) -> bool:
        """Revoga um link temporário"""
        try:
            temp_file = self.temp_file_repo.get_by_download_and_token(download_id, token)
            
            if not temp_file:
                return False
            
            # Deletar do repositório
            success = self.temp_file_repo.delete(temp_file.id)
            
            if success:
                logger.info("Link temporário revogado", 
                           download_id=str(download_id), token=token)
            
            return success
            
        except Exception as e:
            logger.error("Erro ao revogar link temporário", 
                        error=str(e), download_id=str(download_id), token=token)
            return False
    
    def extend_temporary_url(
        self, 
        download_id: UUID, 
        token: str, 
        additional_hours: int = 1
    ) -> Optional[TemporaryFile]:
        """Estende a validade de um link temporário"""
        try:
            temp_file = self.temp_file_repo.get_by_download_and_token(download_id, token)
            
            if not temp_file:
                return None
            
            # Verificar se ainda não expirou
            if datetime.utcnow() > temp_file.expiration_time:
                raise TemporaryFileExpiredError("Link temporário já expirou")
            
            # Estender expiração
            temp_file.expiration_time += timedelta(hours=additional_hours)
            temp_file = self.temp_file_repo.update(temp_file)
            
            logger.info("Link temporário estendido", 
                       download_id=str(download_id),
                       token=token,
                       new_expiration=temp_file.expiration_time.isoformat())
            
            return temp_file
            
        except Exception as e:
            logger.error("Erro ao estender link temporário", 
                        error=str(e), download_id=str(download_id), token=token)
            return None
    
    def get_temporary_url_info(self, download_id: UUID, token: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um link temporário sem validar acesso"""
        try:
            temp_file = self.temp_file_repo.get_by_download_and_token(download_id, token)
            
            if not temp_file:
                return None
            
            return {
                'download_id': str(temp_file.download_id),
                'expiration_time': temp_file.expiration_time.isoformat(),
                'access_count': temp_file.access_count,
                'max_accesses': temp_file.max_accesses,
                'is_expired': datetime.utcnow() > temp_file.expiration_time,
                'is_access_limit_reached': (
                    temp_file.max_accesses and 
                    temp_file.access_count >= temp_file.max_accesses
                ),
                'file_exists': os.path.exists(temp_file.file_path),
                'custom_filename': temp_file.custom_filename
            }
            
        except Exception as e:
            logger.error("Erro ao obter informações do link temporário", 
                        error=str(e), download_id=str(download_id), token=token)
            return None
    
    def cleanup_expired_urls(self) -> int:
        """Remove links temporários expirados"""
        try:
            expired_files = self.temp_file_repo.get_expired_files()
            cleaned_count = 0
            
            for temp_file in expired_files:
                try:
                    # Deletar arquivo físico se necessário
                    if os.path.exists(temp_file.file_path):
                        os.remove(temp_file.file_path)
                        logger.info("Arquivo temporário removido", 
                                   file_path=temp_file.file_path)
                    
                    # Deletar do repositório
                    self.temp_file_repo.delete(temp_file.id)
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.error("Erro ao limpar arquivo temporário", 
                                error=str(e), file_id=str(temp_file.id))
            
            logger.info("Limpeza de links temporários concluída", 
                       cleaned_count=cleaned_count)
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Erro na limpeza de links temporários", error=str(e))
            return 0
    
    def get_access_logs(self, download_id: UUID, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém logs de acesso para um download"""
        try:
            temp_files = self.temp_file_repo.get_by_download_id(download_id)
            
            logs = []
            for temp_file in temp_files:
                logs.append({
                    'token': self._extract_token_from_url(temp_file.temporary_url),
                    'created_at': temp_file.created_at.isoformat(),
                    'expiration_time': temp_file.expiration_time.isoformat(),
                    'access_count': temp_file.access_count,
                    'max_accesses': temp_file.max_accesses,
                    'is_expired': datetime.utcnow() > temp_file.expiration_time
                })
            
            # Ordenar por data de criação (mais recente primeiro)
            logs.sort(key=lambda x: x['created_at'], reverse=True)
            
            return logs[:limit]
            
        except Exception as e:
            logger.error("Erro ao obter logs de acesso", 
                        error=str(e), download_id=str(download_id))
            return []
    
    def _generate_token(self) -> str:
        """Gera um token único para o link temporário"""
        return secrets.token_urlsafe(32)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcula o hash SHA-256 de um arquivo"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _extract_token_from_url(self, url: str) -> str:
        """Extrai o token de uma URL temporária"""
        return url.split('/')[-1]
    
    def get_rate_limit_key(self, download_id: UUID, token: str) -> str:
        """Gera chave para rate limiting"""
        return f"temp_url_rate_limit:{download_id}:{token}"
    
    def check_rate_limit(self, download_id: UUID, token: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """Verifica rate limit para um link temporário"""
        # Esta implementação seria integrada com Redis
        # Por enquanto, retorna True (sem limite)
        return True 