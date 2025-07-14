from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import structlog
from uuid import UUID

from app.domain.entities.download import Download
from app.domain.repositories.download_repository import DownloadRepository
from app.domain.value_objects.download_status import DownloadStatus
from app.infrastructure.database.models import DownloadModel
from app.infrastructure.database.connection import get_db

logger = structlog.get_logger()


class SQLAlchemyDownloadRepository(DownloadRepository):
    """Implementação do DownloadRepository usando SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, download: Download) -> Download:
        """Cria um novo download"""
        try:
            download_model = DownloadModel(
                id=download.id,
                url=download.url,
                status=download.status.value,
                progress=download.progress,
                title=download.title,
                description=download.description,
                duration=download.duration,
                thumbnail=download.thumbnail,
                quality=download.quality.value if download.quality else None,
                format=download.format,
                file_size=download.file_size,
                file_path=download.file_path,
                error_message=download.error_message,
                attempts=download.attempts,
                created_at=download.created_at,
                started_at=download.started_at,
                completed_at=download.completed_at,
                download_count=download.download_count,
                last_accessed=download.last_accessed
            )
            
            self.db.add(download_model)
            self.db.commit()
            self.db.refresh(download_model)
            
            logger.info("Download criado", download_id=str(download.id))
            return self._to_entity(download_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao criar download", error=str(e), download_id=str(download.id))
            raise
    
    def get_by_id(self, download_id: UUID) -> Optional[Download]:
        """Busca um download por ID"""
        try:
            download_model = self.db.query(DownloadModel).filter(
                DownloadModel.id == download_id
            ).first()
            
            if download_model:
                return self._to_entity(download_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar download por ID", error=str(e), download_id=str(download_id))
            raise
    
    def get_by_url(self, url: str) -> Optional[Download]:
        """Busca um download por URL"""
        try:
            download_model = self.db.query(DownloadModel).filter(
                DownloadModel.url == url
            ).first()
            
            if download_model:
                return self._to_entity(download_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar download por URL", error=str(e), url=url)
            raise
    
    def update(self, download: Download) -> Download:
        """Atualiza um download"""
        try:
            download_model = self.db.query(DownloadModel).filter(
                DownloadModel.id == download.id
            ).first()
            
            if not download_model:
                raise ValueError(f"Download não encontrado: {download.id}")
            
            # Atualizar campos
            download_model.status = download.status.value
            download_model.progress = download.progress
            download_model.title = download.title
            download_model.description = download.description
            download_model.duration = download.duration
            download_model.thumbnail = download.thumbnail
            download_model.quality = download.quality.value if download.quality else None
            download_model.format = download.format
            download_model.file_size = download.file_size
            download_model.file_path = download.file_path
            download_model.error_message = download.error_message
            download_model.attempts = download.attempts
            download_model.started_at = download.started_at
            download_model.completed_at = download.completed_at
            download_model.download_count = download.download_count
            download_model.last_accessed = download.last_accessed
            
            self.db.commit()
            self.db.refresh(download_model)
            
            logger.info("Download atualizado", download_id=str(download.id))
            return self._to_entity(download_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao atualizar download", error=str(e), download_id=str(download.id))
            raise
    
    def delete(self, download_id: UUID) -> bool:
        """Deleta um download"""
        try:
            download_model = self.db.query(DownloadModel).filter(
                DownloadModel.id == download_id
            ).first()
            
            if not download_model:
                return False
            
            self.db.delete(download_model)
            self.db.commit()
            
            logger.info("Download deletado", download_id=str(download_id))
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao deletar download", error=str(e), download_id=str(download_id))
            raise
    
    def get_pending_downloads(self, limit: int = 10) -> List[Download]:
        """Busca downloads pendentes"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.PENDING.value
            ).order_by(DownloadModel.created_at.asc()).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads pendentes", error=str(e))
            raise
    
    def get_downloading_downloads(self) -> List[Download]:
        """Busca downloads em andamento"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.DOWNLOADING.value
            ).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads em andamento", error=str(e))
            raise
    
    def get_recent_downloads(self, limit: int = 20) -> List[Download]:
        """Busca downloads recentes"""
        try:
            download_models = self.db.query(DownloadModel).order_by(
                desc(DownloadModel.created_at)
            ).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads recentes", error=str(e))
            raise
    
    def get_downloads_by_status(self, status: DownloadStatus) -> List[Download]:
        """Busca downloads por status"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == status.value
            ).order_by(desc(DownloadModel.created_at)).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads por status", error=str(e), status=status.value)
            raise
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Busca estatísticas dos downloads"""
        try:
            stats = self.db.query(
                DownloadModel.status,
                func.count(DownloadModel.id).label('count')
            ).group_by(DownloadModel.status).all()
            
            result = {
                'total': 0,
                'pending': 0,
                'downloading': 0,
                'completed': 0,
                'failed': 0
            }
            
            for status, count in stats:
                result['total'] += count
                if status in result:
                    result[status] = count
            
            return result
            
        except Exception as e:
            logger.error("Erro ao buscar estatísticas", error=str(e))
            raise
    
    def _to_entity(self, model: DownloadModel) -> Download:
        """Converte modelo SQLAlchemy para entidade do domínio"""
        from app.domain.value_objects.download_quality import DownloadQuality
        
        return Download(
            id=model.id,
            url=model.url,
            status=DownloadStatus(model.status),
            progress=model.progress,
            title=model.title,
            description=model.description,
            duration=model.duration,
            thumbnail=model.thumbnail,
            quality=DownloadQuality(model.quality) if model.quality else None,
            format=model.format,
            file_size=model.file_size,
            file_path=model.file_path,
            error_message=model.error_message,
            attempts=model.attempts,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            download_count=model.download_count,
            last_accessed=model.last_accessed
        ) 