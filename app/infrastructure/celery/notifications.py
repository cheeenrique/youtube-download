from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime
from uuid import UUID
import httpx
import asyncio

from app.shared.config import settings
from app.domain.entities.download import Download
from app.domain.value_objects.download_status import DownloadStatus

logger = structlog.get_logger()


class NotificationService:
    """Serviço para enviar notificações em tempo real via WebSocket"""
    
    def __init__(self):
        self.api_base_url = f"http://api:8000"
    
    async def _send_notification(self, notification_data: Dict[str, Any]):
        """Envia notificação via HTTP para o endpoint do WebSocket"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/notify",
                    json=notification_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("Notificação enviada com sucesso via HTTP", 
                               notification_type=notification_data.get("type"))
                else:
                    logger.error("Erro ao enviar notificação via HTTP", 
                               status_code=response.status_code,
                               response=response.text)
                    
        except Exception as e:
            logger.error("Erro ao enviar notificação via HTTP", error=str(e))
    
    async def notify_download_progress(
        self, 
        download_id: str, 
        progress: float, 
        status: str,
        user_id: str,
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
            
            notification = {
                "type": "download_update",
                "download_id": download_id,
                "user_id": user_id,
                "data": data
            }
            
            await self._send_notification(notification)
            logger.info("Notificação de progresso enviada", download_id=download_id, progress=progress, user_id=user_id)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de progresso", error=str(e), download_id=download_id)
    
    async def notify_download_completed(
        self, 
        download_id: str, 
        file_path: str,
        user_id: str,
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
            
            notification = {
                "type": "download_update",
                "download_id": download_id,
                "user_id": user_id,
                "data": data
            }
            
            await self._send_notification(notification)
            logger.info("Notificação de conclusão enviada", download_id=download_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de conclusão", error=str(e), download_id=download_id)
    
    async def notify_download_failed(
        self, 
        download_id: str, 
        error_message: str,
        user_id: str,
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
            
            notification = {
                "type": "download_update",
                "download_id": download_id,
                "user_id": user_id,
                "data": data
            }
            
            await self._send_notification(notification)
            logger.info("Notificação de falha enviada", download_id=download_id, error=error_message, user_id=user_id)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de falha", error=str(e), download_id=download_id)
    
    async def notify_queue_update(self, queue_data: Dict[str, Any]):
        """Notifica atualização da fila"""
        try:
            notification = {
                "type": "queue_update",
                "data": queue_data
            }
            
            await self._send_notification(notification)
            logger.info("Notificação de fila enviada", queue_data=queue_data)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de fila", error=str(e))
    
    async def notify_stats_update(self, stats_data: Dict[str, Any]):
        """Notifica atualização de estatísticas"""
        try:
            notification = {
                "type": "stats_update",
                "data": stats_data
            }
            
            await self._send_notification(notification)
            logger.info("Notificação de estatísticas enviada", stats_data=stats_data)
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de estatísticas", error=str(e))
    
    async def notify_dashboard_update(
        self,
        downloads_in_progress: List[Dict[str, Any]],
        queue_stats: Dict[str, Any],
        system_stats: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Notifica atualização completa do dashboard"""
        try:
            dashboard_data = {
                "downloads_in_progress": downloads_in_progress,
                "queue_stats": queue_stats,
                "system_stats": system_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            notification = {
                "type": "dashboard_update",
                "user_id": user_id,
                "data": dashboard_data
            }
            
            await self._send_notification(notification)
            logger.info("Notificação de dashboard enviada", 
                       downloads_count=len(downloads_in_progress))
            
        except Exception as e:
            logger.error("Erro ao enviar notificação de dashboard", error=str(e))
    
    async def notify_general_message(self, message_type: str, data: Dict[str, Any]):
        """Envia mensagem geral"""
        try:
            notification = {
                "type": message_type,
                "data": data
            }
            
            await self._send_notification(notification)
            logger.info("Mensagem geral enviada", message_type=message_type)
            
        except Exception as e:
            logger.error("Erro ao enviar mensagem geral", error=str(e))


# Instância global do serviço de notificações
notification_service = NotificationService() 