from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import structlog
from datetime import datetime
from uuid import UUID

from app.domain.repositories.download_repository import DownloadRepository
from app.domain.repositories.download_log_repository import DownloadLogRepository
from app.domain.value_objects.download_status import DownloadStatus

logger = structlog.get_logger()
router = APIRouter(tags=["Server-Sent Events"])


@router.get("/{download_id}/stream")
async def stream_download_progress(download_id: str, request: Request):
    """Stream de progresso de um download específico via SSE"""
    
    async def generate_sse() -> AsyncGenerator[str, None]:
        """Gera eventos SSE para o progresso do download"""
        try:
            # Envia evento inicial
            yield f"data: {json.dumps({'type': 'connection_established', 'download_id': download_id})}\n\n"
            
            # Simula atualizações de progresso (em produção, isso viria do sistema de filas)
            progress = 0
            while progress < 100:
                if await request.is_disconnected():
                    break
                
                # Simula progresso
                progress += 10
                if progress > 100:
                    progress = 100
                
                event_data = {
                    "type": "progress_update",
                    "download_id": download_id,
                    "progress": progress,
                    "status": "downloading" if progress < 100 else "completed",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Aguarda 2 segundos antes da próxima atualização
                import asyncio
                await asyncio.sleep(2)
            
            # Envia evento de conclusão
            completion_data = {
                "type": "download_completed",
                "download_id": download_id,
                "message": "Download concluído",
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            logger.error("Erro no stream SSE", error=str(e))
            error_data = {
                "type": "error",
                "download_id": download_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/queue/stream")
async def stream_queue_status(request: Request):
    """Stream do status da fila via SSE"""
    
    async def generate_queue_sse() -> AsyncGenerator[str, None]:
        """Gera eventos SSE para o status da fila"""
        try:
            # Envia evento inicial
            yield f"data: {json.dumps({'type': 'connection_established', 'message': 'Conectado à fila'})}\n\n"
            
            # Simula atualizações da fila
            queue_position = 0
            while True:
                if await request.is_disconnected():
                    break
                
                queue_data = {
                    "type": "queue_update",
                    "pending": 5,
                    "downloading": 1,
                    "completed": 10,
                    "failed": 2,
                    "total": 18,
                    "queue_position": queue_position,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(queue_data)}\n\n"
                
                # Aguarda 5 segundos antes da próxima atualização
                import asyncio
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error("Erro no stream SSE da fila", error=str(e))
            error_data = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_queue_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/stats/stream")
async def stream_stats(request: Request):
    """Stream de estatísticas via SSE"""
    
    async def generate_stats_sse() -> AsyncGenerator[str, None]:
        """Gera eventos SSE para estatísticas"""
        try:
            # Envia evento inicial
            yield f"data: {json.dumps({'type': 'connection_established', 'message': 'Conectado às estatísticas'})}\n\n"
            
            # Simula atualizações de estatísticas
            while True:
                if await request.is_disconnected():
                    break
                
                stats_data = {
                    "type": "stats_update",
                    "total_downloads": 150,
                    "completed_downloads": 120,
                    "failed_downloads": 10,
                    "pending_downloads": 20,
                    "downloads_today": 15,
                    "downloads_this_week": 45,
                    "downloads_this_month": 180,
                    "total_storage_used": 1024000000,  # 1GB em bytes
                    "average_download_time": 45.5,  # segundos
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(stats_data)}\n\n"
                
                # Aguarda 10 segundos antes da próxima atualização
                import asyncio
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error("Erro no stream SSE de estatísticas", error=str(e))
            error_data = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stats_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.get("/dashboard/stream")
async def stream_dashboard(request: Request):
    """Stream completo do dashboard via SSE com todas as informações em tempo real"""
    
    async def generate_dashboard_sse() -> AsyncGenerator[str, None]:
        """Gera eventos SSE para o dashboard completo"""
        try:
            # Envia evento inicial
            yield f"data: {json.dumps({'type': 'connection_established', 'message': 'Conectado ao dashboard'})}\n\n"
            
            # Simula atualizações do dashboard
            while True:
                if await request.is_disconnected():
                    break
                
                # Simula downloads em progresso com informações detalhadas
                downloads_in_progress = [
                    {
                        "id": "download-1",
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "title": "Rick Astley - Never Gonna Give You Up",
                        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
                        "progress": 45.5,
                        "status": "downloading",
                        "duration": 213,
                        "quality": "best",
                        "file_size": None,
                        "format": None,
                        "started_at": "2024-01-15T10:30:00Z"
                    },
                    {
                        "id": "download-2", 
                        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                        "title": "PSY - GANGNAM STYLE",
                        "thumbnail": "https://img.youtube.com/vi/9bZkp7q19f0/mqdefault.jpg",
                        "progress": 78.2,
                        "status": "downloading",
                        "duration": 252,
                        "quality": "best",
                        "file_size": None,
                        "format": None,
                        "started_at": "2024-01-15T10:25:00Z"
                    },
                    {
                        "id": "download-3",
                        "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
                        "title": "Luis Fonsi - Despacito ft. Daddy Yankee",
                        "thumbnail": "https://img.youtube.com/vi/kJQP7kiw5Fk/mqdefault.jpg",
                        "progress": 12.8,
                        "status": "downloading",
                        "duration": 280,
                        "quality": "best",
                        "file_size": None,
                        "format": None,
                        "started_at": "2024-01-15T10:35:00Z"
                    }
                ]
                
                # Estatísticas da fila
                queue_stats = {
                    "pending": 8,
                    "downloading": 3,
                    "completed": 25,
                    "failed": 2,
                    "total": 38,
                    "queue_position": 5
                }
                
                # Estatísticas do sistema
                system_stats = {
                    "total_downloads": 150,
                    "completed_downloads": 120,
                    "failed_downloads": 10,
                    "pending_downloads": 20,
                    "downloads_today": 15,
                    "downloads_this_week": 45,
                    "downloads_this_month": 180,
                    "total_storage_used": 1024000000,  # 1GB em bytes
                    "average_download_time": 45.5,  # segundos
                    "active_connections": 12,
                    "system_uptime": 86400  # 24 horas em segundos
                }
                
                dashboard_data = {
                    "type": "dashboard_update",
                    "downloads_in_progress": downloads_in_progress,
                    "queue_stats": queue_stats,
                    "system_stats": system_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(dashboard_data)}\n\n"
                
                # Aguarda 3 segundos antes da próxima atualização
                import asyncio
                await asyncio.sleep(3)
                
        except Exception as e:
            logger.error("Erro no stream SSE do dashboard", error=str(e))
            error_data = {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_dashboard_sse(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    ) 