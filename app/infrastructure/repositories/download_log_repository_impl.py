from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, text
import json

from app.domain.repositories.download_log_repository import DownloadLogRepository
from app.domain.entities.download_log import DownloadLog
from app.infrastructure.database.models import DownloadLog
from app.infrastructure.database.connection import SessionLocal


class DownloadLogRepositoryImpl(DownloadLogRepository):
    """Implementação SQLAlchemy do repositório de logs de download"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    async def create(self, download_log: DownloadLog) -> DownloadLog:
        """Cria um novo log de download"""
        db_log = DownloadLog(
            id=download_log.id,
            download_id=download_log.download_id,
            user_id=download_log.user_id,
            session_id=download_log.session_id,
            video_url=download_log.video_url,
            video_title=download_log.video_title,
            video_duration=download_log.video_duration,
            video_size=download_log.video_size,
            video_format=download_log.video_format,
            video_quality=download_log.video_quality,
            start_time=download_log.start_time,
            end_time=download_log.end_time,
            download_duration=download_log.download_duration,
            download_speed=download_log.download_speed,
            file_size_downloaded=download_log.file_size_downloaded,
            progress_percentage=download_log.progress_percentage,
            status=download_log.status,
            error_message=download_log.error_message,
            error_code=download_log.error_code,
            retry_count=download_log.retry_count,
            ip_address=download_log.ip_address,
            user_agent=download_log.user_agent,
            request_headers=download_log.request_headers,
            response_headers=download_log.response_headers,
            download_path=download_log.download_path,
            output_format=download_log.output_format,
            quality_preference=download_log.quality_preference,
            google_drive_uploaded=download_log.google_drive_uploaded,
            google_drive_file_id=download_log.google_drive_file_id,
            google_drive_folder_id=download_log.google_drive_folder_id,
            temporary_url_created=download_log.temporary_url_created,
            temporary_url_id=download_log.temporary_url_id,
            temporary_url_access_count=download_log.temporary_url_access_count,
            memory_usage=download_log.memory_usage,
            cpu_usage=download_log.cpu_usage,
            disk_usage=download_log.disk_usage,
            created_at=download_log.created_at,
            updated_at=download_log.updated_at
        )
        
        self.db_session.add(db_log)
        self.db_session.commit()
        self.db_session.refresh(db_log)
        
        return self._to_entity(db_log)
    
    async def get_by_id(self, log_id: UUID) -> Optional[DownloadLog]:
        """Busca um log por ID"""
        db_log = self.db_session.query(DownloadLog).filter(
            DownloadLog.id == log_id
        ).first()
        
        return self._to_entity(db_log) if db_log else None
    
    async def get_by_download_id(self, download_id: UUID) -> List[DownloadLog]:
        """Busca todos os logs de um download específico"""
        db_logs = self.db_session.query(DownloadLog).filter(
            DownloadLog.download_id == download_id
        ).order_by(desc(DownloadLog.created_at)).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_by_user_id(self, user_id: str, limit: int = 100) -> List[DownloadLog]:
        """Busca logs de um usuário específico"""
        db_logs = self.db_session.query(DownloadLog).filter(
            DownloadLog.user_id == user_id
        ).order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_by_session_id(self, session_id: str) -> List[DownloadLog]:
        """Busca logs de uma sessão específica"""
        db_logs = self.db_session.query(DownloadLog).filter(
            DownloadLog.session_id == session_id
        ).order_by(desc(DownloadLog.created_at)).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_by_status(self, status: str, limit: int = 100) -> List[DownloadLog]:
        """Busca logs por status"""
        db_logs = self.db_session.query(DownloadLog).filter(
            DownloadLog.status == status
        ).order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[DownloadLog]:
        """Busca logs em um intervalo de datas"""
        db_logs = self.db_session.query(DownloadLog).filter(
            and_(
                DownloadLog.created_at >= start_date,
                DownloadLog.created_at <= end_date
            )
        ).order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_failed_downloads(self, limit: int = 100) -> List[DownloadLog]:
        """Busca downloads que falharam"""
        db_logs = self.db_session.query(DownloadLog).filter(
            or_(
                DownloadLog.status.in_(["failed", "error"]),
                DownloadLog.error_message.isnot(None)
            )
        ).order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_successful_downloads(self, limit: int = 100) -> List[DownloadLog]:
        """Busca downloads bem-sucedidos"""
        db_logs = self.db_session.query(DownloadLog).filter(
            DownloadLog.status == "completed"
        ).order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def update(self, download_log: DownloadLog) -> DownloadLog:
        """Atualiza um log existente"""
        db_log = self.db_session.query(DownloadLog).filter(
            DownloadLog.id == download_log.id
        ).first()
        
        if not db_log:
            raise ValueError(f"Log with id {download_log.id} not found")
        
        # Atualiza os campos
        for field, value in download_log.__dict__.items():
            if field != 'id' and hasattr(db_log, field):
                setattr(db_log, field, value)
        
        db_log.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(db_log)
        
        return self._to_entity(db_log)
    
    async def delete(self, log_id: UUID) -> bool:
        """Remove um log"""
        db_log = self.db_session.query(DownloadLog).filter(
            DownloadLog.id == log_id
        ).first()
        
        if db_log:
            self.db_session.delete(db_log)
            self.db_session.commit()
            return True
        
        return False
    
    async def delete_old_logs(self, days: int = 30) -> int:
        """Remove logs antigos (mais de X dias)"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        deleted_count = self.db_session.query(DownloadLog).filter(
            DownloadLog.created_at < cutoff_date
        ).delete()
        
        self.db_session.commit()
        return deleted_count
    
    # Métodos de Analytics
    async def get_download_stats(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas gerais de downloads"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        total_downloads = query.count()
        
        # Downloads por status
        status_stats = self.db_session.query(
            DownloadLog.status,
            func.count(DownloadLog.id).label('count')
        ).group_by(DownloadLog.status).all()
        
        # Downloads por dia
        daily_stats = self.db_session.query(
            func.date(DownloadLog.created_at).label('date'),
            func.count(DownloadLog.id).label('count')
        ).group_by(func.date(DownloadLog.created_at)).order_by(
            func.date(DownloadLog.created_at)
        ).all()
        
        return {
            "total_downloads": total_downloads,
            "status_distribution": {status: count for status, count in status_stats},
            "daily_downloads": [{"date": str(date), "count": count} for date, count in daily_stats],
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna métricas de performance"""
        query = self.db_session.query(DownloadLog).filter(
            DownloadLog.download_duration.isnot(None)
        )
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        # Estatísticas de duração
        duration_stats = query.with_entities(
            func.avg(DownloadLog.download_duration).label('avg_duration'),
            func.min(DownloadLog.download_duration).label('min_duration'),
            func.max(DownloadLog.download_duration).label('max_duration'),
            func.avg(DownloadLog.download_speed).label('avg_speed'),
            func.avg(DownloadLog.file_size_downloaded).label('avg_file_size')
        ).first()
        
        return {
            "average_duration_seconds": float(duration_stats.avg_duration) if duration_stats.avg_duration else 0,
            "min_duration_seconds": float(duration_stats.min_duration) if duration_stats.min_duration else 0,
            "max_duration_seconds": float(duration_stats.max_duration) if duration_stats.max_duration else 0,
            "average_speed_mbps": float(duration_stats.avg_speed) if duration_stats.avg_speed else 0,
            "average_file_size_bytes": float(duration_stats.avg_file_size) if duration_stats.avg_file_size else 0,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_error_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna análise de erros"""
        query = self.db_session.query(DownloadLog).filter(
            or_(
                DownloadLog.status.in_(["failed", "error"]),
                DownloadLog.error_message.isnot(None)
            )
        )
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        total_errors = query.count()
        
        # Erros por código
        error_codes = query.with_entities(
            DownloadLog.error_code,
            func.count(DownloadLog.id).label('count')
        ).group_by(DownloadLog.error_code).all()
        
        # Erros por dia
        daily_errors = query.with_entities(
            func.date(DownloadLog.created_at).label('date'),
            func.count(DownloadLog.id).label('count')
        ).group_by(func.date(DownloadLog.created_at)).order_by(
            func.date(DownloadLog.created_at)
        ).all()
        
        return {
            "total_errors": total_errors,
            "error_codes": {code: count for code, count in error_codes if code},
            "daily_errors": [{"date": str(date), "count": count} for date, count in daily_errors],
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_user_activity(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna atividade do usuário"""
        query = self.db_session.query(DownloadLog)
        
        if user_id:
            query = query.filter(DownloadLog.user_id == user_id)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        # Usuários mais ativos
        active_users = query.with_entities(
            DownloadLog.user_id,
            func.count(DownloadLog.id).label('download_count'),
            func.sum(DownloadLog.file_size_downloaded).label('total_size')
        ).group_by(DownloadLog.user_id).order_by(
            desc(func.count(DownloadLog.id))
        ).limit(10).all()
        
        return {
            "active_users": [
                {
                    "user_id": user_id,
                    "download_count": count,
                    "total_size_bytes": float(total_size) if total_size else 0
                }
                for user_id, count, total_size in active_users if user_id
            ],
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_popular_videos(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Retorna vídeos mais populares"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        popular_videos = query.with_entities(
            DownloadLog.video_url,
            DownloadLog.video_title,
            func.count(DownloadLog.id).label('download_count'),
            func.avg(DownloadLog.download_duration).label('avg_duration')
        ).group_by(
            DownloadLog.video_url,
            DownloadLog.video_title
        ).order_by(desc(func.count(DownloadLog.id))).limit(limit).all()
        
        return [
            {
                "video_url": video_url,
                "video_title": video_title,
                "download_count": count,
                "average_duration_seconds": float(avg_duration) if avg_duration else 0
            }
            for video_url, video_title, count, avg_duration in popular_videos
        ]
    
    async def get_quality_preferences(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Retorna preferências de qualidade"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        quality_stats = query.with_entities(
            DownloadLog.video_quality,
            func.count(DownloadLog.id).label('count')
        ).group_by(DownloadLog.video_quality).all()
        
        return {quality: count for quality, count in quality_stats}
    
    async def get_format_usage(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Retorna uso de formatos"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        format_stats = query.with_entities(
            DownloadLog.video_format,
            func.count(DownloadLog.id).label('count')
        ).group_by(DownloadLog.video_format).all()
        
        return {format_type: count for format_type, count in format_stats}
    
    async def get_google_drive_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas do Google Drive"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        total_uploads = query.filter(DownloadLog.google_drive_uploaded == True).count()
        total_downloads = query.count()
        
        return {
            "total_uploads": total_uploads,
            "total_downloads": total_downloads,
            "upload_percentage": (total_uploads / total_downloads * 100) if total_downloads > 0 else 0,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_temporary_url_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna estatísticas de URLs temporárias"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        total_temp_urls = query.filter(DownloadLog.temporary_url_created == True).count()
        total_accesses = query.with_entities(
            func.sum(DownloadLog.temporary_url_access_count)
        ).scalar() or 0
        
        return {
            "total_temporary_urls": total_temp_urls,
            "total_accesses": int(total_accesses),
            "average_accesses_per_url": (total_accesses / total_temp_urls) if total_temp_urls > 0 else 0,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def get_system_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Retorna métricas do sistema"""
        query = self.db_session.query(DownloadLog)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        # Métricas de sistema
        system_stats = query.with_entities(
            func.avg(DownloadLog.memory_usage).label('avg_memory'),
            func.avg(DownloadLog.cpu_usage).label('avg_cpu'),
            func.avg(DownloadLog.disk_usage).label('avg_disk'),
            func.max(DownloadLog.memory_usage).label('max_memory'),
            func.max(DownloadLog.cpu_usage).label('max_cpu'),
            func.max(DownloadLog.disk_usage).label('max_disk')
        ).first()
        
        return {
            "average_memory_usage": float(system_stats.avg_memory) if system_stats.avg_memory else 0,
            "average_cpu_usage": float(system_stats.avg_cpu) if system_stats.avg_cpu else 0,
            "average_disk_usage": float(system_stats.avg_disk) if system_stats.avg_disk else 0,
            "max_memory_usage": float(system_stats.max_memory) if system_stats.max_memory else 0,
            "max_cpu_usage": float(system_stats.max_cpu) if system_stats.max_cpu else 0,
            "max_disk_usage": float(system_stats.max_disk) if system_stats.max_disk else 0,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    
    async def search_logs(
        self,
        query: str,
        limit: int = 100
    ) -> List[DownloadLog]:
        """Busca logs por texto"""
        db_logs = self.db_session.query(DownloadLog).filter(
            or_(
                DownloadLog.video_title.ilike(f"%{query}%"),
                DownloadLog.video_url.ilike(f"%{query}%"),
                DownloadLog.error_message.ilike(f"%{query}%"),
                DownloadLog.user_id.ilike(f"%{query}%")
            )
        ).order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    async def get_audit_trail(
        self,
        download_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[DownloadLog]:
        """Retorna trilha de auditoria"""
        query = self.db_session.query(DownloadLog)
        
        if download_id:
            query = query.filter(DownloadLog.download_id == download_id)
        
        if user_id:
            query = query.filter(DownloadLog.user_id == user_id)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    DownloadLog.created_at >= start_date,
                    DownloadLog.created_at <= end_date
                )
            )
        
        db_logs = query.order_by(desc(DownloadLog.created_at)).limit(limit).all()
        
        return [self._to_entity(log) for log in db_logs]
    
    def _to_entity(self, db_log: DownloadLog) -> DownloadLog:
        """Converte modelo SQLAlchemy para entidade"""
        if not db_log:
            return None
        
        return DownloadLog(
            id=db_log.id,
            download_id=db_log.download_id,
            user_id=db_log.user_id,
            session_id=db_log.session_id,
            video_url=db_log.video_url,
            video_title=db_log.video_title,
            video_duration=db_log.video_duration,
            video_size=db_log.video_size,
            video_format=db_log.video_format,
            video_quality=db_log.video_quality,
            start_time=db_log.start_time,
            end_time=db_log.end_time,
            download_duration=db_log.download_duration,
            download_speed=db_log.download_speed,
            file_size_downloaded=db_log.file_size_downloaded,
            progress_percentage=db_log.progress_percentage,
            status=db_log.status,
            error_message=db_log.error_message,
            error_code=db_log.error_code,
            retry_count=db_log.retry_count,
            ip_address=db_log.ip_address,
            user_agent=db_log.user_agent,
            request_headers=db_log.request_headers,
            response_headers=db_log.response_headers,
            download_path=db_log.download_path,
            output_format=db_log.output_format,
            quality_preference=db_log.quality_preference,
            google_drive_uploaded=db_log.google_drive_uploaded,
            google_drive_file_id=db_log.google_drive_file_id,
            google_drive_folder_id=db_log.google_drive_folder_id,
            temporary_url_created=db_log.temporary_url_created,
            temporary_url_id=db_log.temporary_url_id,
            temporary_url_access_count=db_log.temporary_url_access_count,
            memory_usage=db_log.memory_usage,
            cpu_usage=db_log.cpu_usage,
            disk_usage=db_log.disk_usage,
            created_at=db_log.created_at,
            updated_at=db_log.updated_at
        ) 
