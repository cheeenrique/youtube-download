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
    
    async def create(self, download: Download) -> Download:
        """Cria um novo download"""
        try:
            download_model = DownloadModel(
                id=download.id,
                user_id=download.user_id,
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
                download_count=download.downloads_count,
                last_accessed=download.last_accessed,
                storage_type=download.storage_type
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
    
    async def get_by_id(self, download_id: UUID) -> Optional[Download]:
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
    
    async def get_by_url(self, url: str) -> Optional[Download]:
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
    
    async def update(self, download: Download) -> Download:
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
            download_model.download_count = download.downloads_count
            download_model.last_accessed = download.last_accessed
            
            self.db.commit()
            self.db.refresh(download_model)
            
            logger.info("Download atualizado", download_id=str(download.id))
            return self._to_entity(download_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao atualizar download", error=str(e), download_id=str(download.id))
            raise
    
    async def delete(self, download_id: UUID) -> bool:
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

    async def list_all(self, limit: int = 100, offset: int = 0, user_id: Optional[UUID] = None) -> List[Download]:
        """Lista todos os downloads, opcionalmente filtrados por usuário"""
        try:
            query = self.db.query(DownloadModel)
            
            if user_id:
                query = query.filter(DownloadModel.user_id == user_id)
            
            download_models = query.order_by(
                desc(DownloadModel.created_at)
            ).offset(offset).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao listar downloads", error=str(e))
            raise

    async def list_by_user(self, user_id: UUID, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads de um usuário específico"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.user_id == user_id
            ).order_by(desc(DownloadModel.created_at)).offset(offset).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao listar downloads do usuário", error=str(e), user_id=str(user_id))
            raise

    async def list_by_status(self, status: DownloadStatus, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads por status"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == status.value
            ).order_by(desc(DownloadModel.created_at)).offset(offset).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao listar downloads por status", error=str(e), status=status.value)
            raise

    async def list_pending_downloads(self, limit: int = 10) -> List[Download]:
        """Lista downloads pendentes para processamento"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.PENDING.value
            ).order_by(DownloadModel.created_at.asc()).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao listar downloads pendentes", error=str(e))
            raise

    async def list_failed_downloads(self, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads que falharam"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.FAILED.value
            ).order_by(desc(DownloadModel.created_at)).offset(offset).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao listar downloads falhados", error=str(e))
            raise

    async def list_completed_downloads(self, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads concluídos"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.COMPLETED.value
            ).order_by(desc(DownloadModel.created_at)).offset(offset).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao listar downloads concluídos", error=str(e))
            raise

    async def count_by_status(self, status: DownloadStatus) -> int:
        """Conta downloads por status"""
        try:
            count = self.db.query(DownloadModel).filter(
                DownloadModel.status == status.value
            ).count()
            
            return count
            
        except Exception as e:
            logger.error("Erro ao contar downloads por status", error=str(e), status=status.value)
            raise

    async def cleanup_expired_downloads(self, expiration_hours: int = 24) -> int:
        """Remove downloads expirados e retorna a quantidade removida"""
        try:
            expiration_time = datetime.utcnow() - timedelta(hours=expiration_hours)
            
            expired_downloads = self.db.query(DownloadModel).filter(
                and_(
                    DownloadModel.created_at < expiration_time,
                    DownloadModel.status.in_([DownloadStatus.FAILED.value, DownloadStatus.COMPLETED.value])
                )
            ).all()
            
            count = len(expired_downloads)
            
            for download in expired_downloads:
                self.db.delete(download)
            
            self.db.commit()
            
            logger.info("Downloads expirados removidos", count=count, expiration_hours=expiration_hours)
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao limpar downloads expirados", error=str(e))
            raise

    async def search_downloads(self, query: str, limit: int = 100, offset: int = 0) -> List[Download]:
        """Busca downloads por título ou descrição"""
        try:
            search_term = f"%{query}%"
            download_models = self.db.query(DownloadModel).filter(
                or_(
                    DownloadModel.title.ilike(search_term),
                    DownloadModel.description.ilike(search_term)
                )
            ).order_by(desc(DownloadModel.created_at)).offset(offset).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads", error=str(e), query=query)
            raise
    
    def get_pending_downloads(self, limit: int = 10) -> List[Download]:
        """Busca downloads pendentes (método síncrono para compatibilidade)"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.PENDING.value
            ).order_by(DownloadModel.created_at.asc()).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads pendentes", error=str(e))
            raise
    
    def get_downloading_downloads(self) -> List[Download]:
        """Busca downloads em andamento (método síncrono para compatibilidade)"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == DownloadStatus.DOWNLOADING.value
            ).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads em andamento", error=str(e))
            raise
    
    def get_recent_downloads(self, limit: int = 20) -> List[Download]:
        """Busca downloads recentes (método síncrono para compatibilidade)"""
        try:
            download_models = self.db.query(DownloadModel).order_by(
                desc(DownloadModel.created_at)
            ).limit(limit).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads recentes", error=str(e))
            raise
    
    def get_downloads_by_status(self, status: DownloadStatus) -> List[Download]:
        """Busca downloads por status (método síncrono para compatibilidade)"""
        try:
            download_models = self.db.query(DownloadModel).filter(
                DownloadModel.status == status.value
            ).order_by(desc(DownloadModel.created_at)).all()
            
            return [self._to_entity(model) for model in download_models]
            
        except Exception as e:
            logger.error("Erro ao buscar downloads por status", error=str(e), status=status.value)
            raise
    
    async def get_download_stats(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Busca estatísticas dos downloads"""
        try:
            from datetime import datetime, timedelta
            
            # Query base
            base_query = self.db.query(DownloadModel)
            
            # Filtrar por usuário se especificado
            if user_id:
                base_query = base_query.filter(DownloadModel.user_id == user_id)
            
            # Estatísticas por status
            stats = base_query.with_entities(
                DownloadModel.status,
                func.count(DownloadModel.id).label('count')
            ).group_by(DownloadModel.status).all()
            
            # Contadores por status
            pending = 0
            downloading = 0
            completed = 0
            failed = 0
            total = 0
            
            for status, count in stats:
                total += count
                if status == DownloadStatus.PENDING.value:
                    pending = count
                elif status == DownloadStatus.DOWNLOADING.value:
                    downloading = count
                elif status == DownloadStatus.COMPLETED.value:
                    completed = count
                elif status == DownloadStatus.FAILED.value:
                    failed = count
            
            # Downloads por período
            today = datetime.utcnow().date()
            week_ago = datetime.utcnow() - timedelta(days=7)
            month_ago = datetime.utcnow() - timedelta(days=30)
            
            downloads_today = base_query.filter(
                func.date(DownloadModel.created_at) == today
            ).count()
            
            downloads_this_week = base_query.filter(
                DownloadModel.created_at >= week_ago
            ).count()
            
            downloads_this_month = base_query.filter(
                DownloadModel.created_at >= month_ago
            ).count()
            
            # Estatísticas de armazenamento e tempo
            completed_downloads = base_query.filter(
                DownloadModel.status == DownloadStatus.COMPLETED.value
            ).all()
            
            total_storage_used = sum(d.file_size or 0 for d in completed_downloads)
            
            # Tempo médio de download
            download_times = []
            for download in completed_downloads:
                if download.started_at and download.completed_at:
                    duration = (download.completed_at - download.started_at).total_seconds()
                    download_times.append(duration)
            
            average_download_time = sum(download_times) / len(download_times) if download_times else 0.0
            
            return {
                'total_downloads': total,
                'completed_downloads': completed,
                'failed_downloads': failed,
                'pending_downloads': pending,
                'downloads_today': downloads_today,
                'downloads_this_week': downloads_this_week,
                'downloads_this_month': downloads_this_month,
                'total_storage_used': total_storage_used,
                'average_download_time': average_download_time
            }
            
        except Exception as e:
            logger.error("Erro ao buscar estatísticas", error=str(e))
            raise
    
    def _to_entity(self, model: DownloadModel) -> Download:
        """Converte modelo SQLAlchemy para entidade do domínio"""
        from app.domain.value_objects.download_quality import DownloadQuality
        
        return Download(
            id=model.id,
            user_id=model.user_id,
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
            downloads_count=model.download_count,
            last_accessed=model.last_accessed,
            storage_type=model.storage_type
        ) 