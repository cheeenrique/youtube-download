from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
import json
import structlog
from uuid import UUID

from app.infrastructure.websocket import manager
from app.domain.repositories.download_repository import DownloadRepository

logger = structlog.get_logger()
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/downloads/{download_id}")
async def websocket_download(websocket: WebSocket, download_id: str):
    """WebSocket para monitoramento de um download específico"""
    try:
        await manager.connect_download(websocket, download_id)
        
        # Envia mensagem inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "download_id": download_id,
            "message": "Conectado ao download"
        }))
        
        # Mantém a conexão ativa
        while True:
            try:
                # Aguarda mensagens do cliente (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Erro no WebSocket de download", error=str(e))
                break
                
    except Exception as e:
        logger.error("Erro ao conectar WebSocket de download", error=str(e))
    finally:
        await manager.disconnect_download(websocket, download_id)


@router.websocket("/ws/queue")
async def websocket_queue(websocket: WebSocket):
    """WebSocket para monitoramento da fila de downloads"""
    try:
        await manager.connect_queue(websocket)
        
        # Envia mensagem inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado à fila de downloads"
        }))
        
        # Mantém a conexão ativa
        while True:
            try:
                # Aguarda mensagens do cliente (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Erro no WebSocket da fila", error=str(e))
                break
                
    except Exception as e:
        logger.error("Erro ao conectar WebSocket da fila", error=str(e))
    finally:
        await manager.disconnect_queue(websocket)


@router.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """WebSocket para monitoramento de estatísticas"""
    try:
        await manager.connect_stats(websocket)
        
        # Envia mensagem inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado às estatísticas"
        }))
        
        # Mantém a conexão ativa
        while True:
            try:
                # Aguarda mensagens do cliente (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Erro no WebSocket de estatísticas", error=str(e))
                break
                
    except Exception as e:
        logger.error("Erro ao conectar WebSocket de estatísticas", error=str(e))
    finally:
        await manager.disconnect_stats(websocket)


@router.websocket("/ws/general")
async def websocket_general(websocket: WebSocket):
    """WebSocket para mensagens gerais"""
    try:
        await manager.connect_general(websocket)
        
        # Envia mensagem inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado às mensagens gerais"
        }))
        
        # Mantém a conexão ativa
        while True:
            try:
                # Aguarda mensagens do cliente (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Erro no WebSocket geral", error=str(e))
                break
                
    except Exception as e:
        logger.error("Erro ao conectar WebSocket geral", error=str(e))
    finally:
        await manager.disconnect_general(websocket)


@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket para dashboard completo com todas as informações em tempo real"""
    try:
        await manager.connect_dashboard(websocket)
        
        # Envia mensagem inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado ao dashboard completo"
        }))
        
        # Mantém a conexão ativa
        while True:
            try:
                # Aguarda mensagens do cliente (ping/pong)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error("Erro no WebSocket do dashboard", error=str(e))
                break
                
    except Exception as e:
        logger.error("Erro ao conectar WebSocket do dashboard", error=str(e))
    finally:
        await manager.disconnect_dashboard(websocket)


@router.get("/ws/connections")
async def get_connection_count():
    """Retorna contagem de conexões WebSocket ativas"""
    return manager.get_connection_count() 