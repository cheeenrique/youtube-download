from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
from uuid import UUID

from app.infrastructure.websocket import manager
from app.domain.entities.download import Download
from app.domain.value_objects.download_status import DownloadStatus

logger = structlog.get_logger()


class NotificationService:
    """Serviço para enviar notificações em tempo real via WebSocket"""
    
    async def notify_download_progress(
        self, 
        download_id: str, 
        progress: float, 
        status: str,
        title: Optional[str] = None,
        thumbnail: Optional[str] = None,
        url: Optional[str] = None
    ):
        """Notifica progresso de um download específico"""
        try:
            data = {
                "progress": progress,
                "status": status,
                "title": title,
                "thumbnail": thumbnail,
                "url": url
            }
            
            await manager.send_download_update(download_id, data)
            logger.info("Notificação de progresso enviada", download_id=download_id, progress=progress)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de progresso", error=str(e), download_id=download_id)
    
    async def notify_download_completed(
        self, 
        download_id: str, 
        file_path: str,
        title: Optional[str] = None,
        thumbnail: Optional[str] = None,
        url: Optional[str] = None,
        file_size: Optional[int] = None,
        format: Optional[str] = None
    ):
        """Notifica conclusão de um download"""
        try:
            data = {
                "progress": 100.0,
                "status": "completed",
                "file_path": file_path,
                "title": title,
                "thumbnail": thumbnail,
                "url": url,
                "file_size": file_size,
                "format": format
            }
            
            await manager.send_download_update(download_id, data)
            logger.info("Notificação de conclusão enviada", download_id=download_id)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de conclusão", error=str(e), download_id=download_id)
    
    async def notify_download_failed(
        self, 
        download_id: str, 
        error_message: str,
        title: Optional[str] = None,
        thumbnail: Optional[str] = None,
        url: Optional[str] = None
    ):
        """Notifica falha de um download"""
        try:
            data = {
                "progress": 0.0,
                "status": "failed",
                "error_message": error_message,
                "title": title,
                "thumbnail": thumbnail,
                "url": url
            }
            
            await manager.send_download_update(download_id, data)
            logger.info("Notificação de falha enviada", download_id=download_id, error=error_message)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de falha", error=str(e), download_id=download_id)
    
    async def notify_queue_update(self, queue_data: Dict[str, Any]):
        """Notifica atualização da fila"""
        try:
            await manager.send_queue_update(queue_data)
            logger.info("Notificação de fila enviada", queue_data=queue_data)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de fila", error=str(e))
    
    async def notify_stats_update(self, stats_data: Dict[str, Any]):
        """Notifica atualização de estatísticas"""
        try:
            await manager.send_stats_update(stats_data)
            logger.info("Notificação de estatísticas enviada", stats_data=stats_data)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de estatísticas", error=str(e))
    
    async def notify_dashboard_update(
        self,
        downloads_in_progress: List[Dict[str, Any]],
        queue_stats: Dict[str, Any],
        system_stats: Dict[str, Any]
    ):
        """Notifica atualização completa do dashboard"""
        try:
            dashboard_data = {
                "downloads_in_progress": downloads_in_progress,
                "queue_stats": queue_stats,
                "system_stats": system_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await manager.send_dashboard_update(dashboard_data)
            logger.info("Notificação de dashboard enviada", 
                       downloads_count=len(downloads_in_progress))
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de dashboard", error=str(e))
    
    async def notify_general_message(self, message_type: str, data: Dict[str, Any]):
        """Envia mensagem geral"""
        try:
            await manager.send_general_message(message_type, data)
            logger.info("Mensagem geral enviada", message_type=message_type)
            
        except Exception as e:
            logger.error("Erro ao enviar mensagem geral", error=str(e))


# Instância global do serviço de notificações
notification_service = NotificationService() 