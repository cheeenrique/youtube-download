from typing import Dict, Any, Optional
from celery import current_task
import structlog
from datetime import datetime, timedelta, timezone
import os
import yt_dlp
from uuid import UUID
import asyncio

from app.infrastructure.celery.celery_app import celery_app
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.repositories.download_repository_impl import SQLAlchemyDownloadRepository
from app.domain.entities.download import Download
from app.domain.value_objects.download_status import DownloadStatus
from app.domain.value_objects.download_quality import DownloadQuality
from app.infrastructure.celery.notifications import notification_service
from app.shared.config import settings

logger = structlog.get_logger()


class ProgressHook:
    """Hook para capturar progresso do yt-dlp"""
    
    def __init__(self, download_id: str, notification_service):
        self.download_id = download_id
        self.notification_service = notification_service
        self.last_progress = 0
    
    def __call__(self, d):
        if d['status'] == 'downloading':
            # Calcular progresso
            if 'total_bytes' in d and d['total_bytes']:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                progress = self.last_progress
            
            # Atualizar apenas se o progresso mudou significativamente
            if abs(progress - self.last_progress) >= 1:
                self.last_progress = progress
                current_task.update_state(
                    state='PROGRESS',
                    meta={'progress': progress, 'status': 'downloading'}
                )
                
                # Enviar notificação
                self.notification_service.notify_download_progress(
                    self.download_id, progress, 'downloading'
                )
        
        elif d['status'] == 'finished':
            current_task.update_state(
                state='PROGRESS',
                meta={'progress': 100, 'status': 'finished'}
            )


@celery_app.task(bind=True, name="download_video")
def download_video_task(self, download_id: str, url: str, quality: str = "best"):
    """Task para download de vídeo"""
    db = SessionLocal()
    try:
        # Buscar download no banco
        repo = SQLAlchemyDownloadRepository(db)
        download = repo.get_by_id(UUID(download_id))
        
        if not download:
            raise ValueError(f"Download não encontrado: {download_id}")
        
        # Atualizar status para downloading
        download.status = DownloadStatus.DOWNLOADING
        download.started_at = datetime.now(timezone.utc)
        download.attempts += 1
        repo.update(download)
        
        # Notificar início
        asyncio.run(notification_service.notify_download_progress(
            download_id, 0, 'downloading'
        ))
        
        # Configurar yt-dlp
        ydl_opts = {
            'format': quality,
            'outtmpl': os.path.join(settings.videos_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [ProgressHook(download_id, notification_service)],
            'writethumbnail': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'quiet': False,
        }
        
        # Download do vídeo
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extrair informações
            info = ydl.extract_info(url, download=False)
            
            # Atualizar metadados
            download.title = info.get('title')
            download.description = info.get('description')
            download.duration = info.get('duration')
            download.thumbnail = info.get('thumbnail')
            download.quality = DownloadQuality(quality)
            download.format = info.get('ext')
            
            # Download real
            ydl.download([url])
            
            # Buscar arquivo baixado
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                download.file_path = filename
                download.file_size = os.path.getsize(filename)
                download.status = DownloadStatus.COMPLETED
                download.completed_at = datetime.now(timezone.utc)
                download.progress = 100.0
                
                # Atualizar no banco
                repo.update(download)
                
                # Notificar conclusão
                asyncio.run(notification_service.notify_download_completed(
                    download_id,
                    download.file_path,
                    download.title,
                    download.thumbnail,
                    url,
                    download.file_size,
                    download.format
                ))
                
                logger.info("Download concluído", 
                           download_id=download_id,
                           file_path=download.file_path,
                           file_size=download.file_size)
                
                return {
                    'status': 'completed',
                    'file_path': download.file_path,
                    'file_size': download.file_size
                }
            else:
                raise FileNotFoundError(f"Arquivo não encontrado: {filename}")
                
    except Exception as e:
        logger.error("Erro no download", 
                    download_id=download_id,
                    error=str(e))
        
        # Atualizar status de erro
        if 'download' in locals():
            download.status = DownloadStatus.FAILED
            download.error_message = str(e)
            repo.update(download)
            
            # Notificar erro
            asyncio.run(notification_service.notify_download_failed(
                download_id, str(e)
            ))
        
        # Re-raise para o Celery
        raise
    
    finally:
        db.close()


@celery_app.task(name="update_download_stats")
def update_download_stats_task():
    """Task para atualizar estatísticas dos downloads"""
    db = SessionLocal()
    try:
        repo = SQLAlchemyDownloadRepository(db)
        stats = repo.get_download_stats()
        
        # Notificar atualização de estatísticas
        asyncio.run(notification_service.notify_stats_update(stats))
        
        logger.info("Estatísticas atualizadas", stats=stats)
        return stats
        
    except Exception as e:
        logger.error("Erro ao atualizar estatísticas", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="process_download_queue")
def process_download_queue_task():
    """Task para processar a fila de downloads"""
    db = SessionLocal()
    try:
        repo = SQLAlchemyDownloadRepository(db)
        
        # Buscar downloads pendentes
        pending_downloads = repo.get_pending_downloads(limit=1)
        
        if pending_downloads:
            download = pending_downloads[0]
            
            # Iniciar download
            download_video_task.delay(
                str(download.id),
                download.url,
                download.quality.value if download.quality else "best"
            )
            
            logger.info("Download iniciado da fila", download_id=str(download.id))
            return {"status": "started", "download_id": str(download.id)}
        else:
            logger.info("Nenhum download pendente na fila")
            return {"status": "no_pending_downloads"}
            
    except Exception as e:
        logger.error("Erro ao processar fila", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="retry_failed_downloads")
def retry_failed_downloads_task():
    """Task para tentar novamente downloads que falharam"""
    db = SessionLocal()
    try:
        repo = SQLAlchemyDownloadRepository(db)
        
        # Buscar downloads que falharam
        failed_downloads = repo.get_downloads_by_status(DownloadStatus.FAILED)
        
        retried_count = 0
        for download in failed_downloads:
            if download.attempts < 3:  # Máximo 3 tentativas
                # Resetar status
                download.status = DownloadStatus.PENDING
                download.error_message = None
                repo.update(download)
                
                # Adicionar à fila
                download_video_task.delay(
                    str(download.id),
                    download.url,
                    download.quality.value if download.quality else "best"
                )
                
                retried_count += 1
        
        logger.info("Downloads com falha reprocessados", count=retried_count)
        return {"status": "retried", "count": retried_count}
        
    except Exception as e:
        logger.error("Erro ao reprocessar downloads", error=str(e))
        raise
    
    finally:
        db.close() 