from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, BackgroundTasks
from typing import Optional, Dict, Any
import json
import structlog
from uuid import UUID

from app.infrastructure.websocket import manager
from app.domain.repositories.download_repository import DownloadRepository
from app.presentation.api.v1.auth import verify_token
from app.infrastructure.database.connection import get_db
from app.infrastructure.repositories.user_repository_impl import SQLAlchemyUserRepository
from sqlalchemy.orm import Session

logger = structlog.get_logger()
router = APIRouter(tags=["WebSocket"])


async def authenticate_websocket(websocket: WebSocket, db: Session) -> Optional[dict]:
    """Autentica o WebSocket usando token JWT"""
    try:
        # Aceitar a conexão primeiro
        await websocket.accept()
        
        # Aguardar mensagem de autenticação
        data = await websocket.receive_text()
        message = json.loads(data)
        
        if message.get("type") != "auth":
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Autenticação necessária"
            }))
            await websocket.close()
            return None
        
        token = message.get("token")
        if not token:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Token não fornecido"
            }))
            await websocket.close()
            return None
        
        # Verificar token
        user_data = verify_token(token)
        if not user_data:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Token inválido"
            }))
            await websocket.close()
            return None
        
        # Buscar informações do usuário no banco
        user_id = user_data.get("user_id")
        user_repo = SQLAlchemyUserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Usuário não encontrado"
            }))
            await websocket.close()
            return None
        
        # Enviar confirmação de autenticação
        await websocket.send_text(json.dumps({
            "type": "auth_success",
            "message": "Autenticado com sucesso",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role.value
            }
        }))
        
        return user_data
        
    except Exception as e:
        logger.error("Erro na autenticação do WebSocket", error=str(e))
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Erro na autenticação"
            }))
            await websocket.close()
        except:
            pass
        return None


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
async def websocket_dashboard(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket para dashboard completo com todas as informações em tempo real"""
    try:
        # Autenticar o WebSocket
        user_data = await authenticate_websocket(websocket, db)
        if not user_data:
            return
        
        # Adicionar ao manager (sem aceitar novamente)
        await manager.connect_dashboard(websocket, user_data.get("user_id"))
        
        # Envia mensagem inicial
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Conectado ao dashboard completo",
            "user_id": user_data.get("user_id")
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


@router.post("/ws/connections/clear")
async def clear_all_connections():
    """Limpa todas as conexões WebSocket ativas"""
    try:
        await manager.clear_all_connections()
        return {"message": "Todas as conexões WebSocket foram limpas", "status": "success"}
    except Exception as e:
        logger.error("Erro ao limpar conexões", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao limpar conexões")


@router.post("/ws/connections/disconnect-user/{user_id}")
async def disconnect_user_connections(user_id: str):
    """Desconecta todas as conexões de um usuário específico"""
    try:
        await manager.disconnect_user(user_id)
        return {"message": f"Conexões do usuário {user_id} desconectadas", "status": "success"}
    except Exception as e:
        logger.error("Erro ao desconectar usuário", error=str(e), user_id=user_id)
        raise HTTPException(status_code=500, detail="Erro ao desconectar usuário")


@router.post("/ws/connections/disconnect-me")
async def disconnect_current_user_connections(request: Request):
    """Desconecta todas as conexões do usuário atual (para logout)"""
    try:
        # Extrair token do header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token não fornecido")
        
        token = auth_header.split(" ")[1]
        
        # Verificar token
        user_data = verify_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = user_data.get("user_id")
        if user_id:
            await manager.disconnect_user(user_id)
            return {"message": "Suas conexões foram desconectadas", "status": "success"}
        else:
            raise HTTPException(status_code=400, detail="ID do usuário não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao desconectar usuário atual", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao desconectar usuário")


@router.post("/ws/test-notification")
async def test_notification(request: Request):
    """Endpoint de teste para enviar notificação manualmente"""
    try:
        # Extrair token do header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token não fornecido")
        
        token = auth_header.split(" ")[1]
        
        # Verificar token
        user_data = verify_token(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = user_data.get("user_id")
        
        # Obter dados do corpo da requisição
        body = await request.json()
        download_id = body.get("download_id")
        data = body.get("data", {})
        
        if not download_id:
            raise HTTPException(status_code=400, detail="download_id é obrigatório")
        
        # Enviar notificação
        await manager.send_download_update(download_id, data, user_id)
        
        logger.info("Notificação de teste enviada", download_id=download_id, user_id=user_id)
        
        return {
            "message": "Notificação de teste enviada com sucesso",
            "download_id": download_id,
            "user_id": user_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao enviar notificação de teste", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao enviar notificação de teste") 


@router.post("/notify")
async def send_notification(
    notification: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Endpoint para o Celery enviar notificações para o WebSocket Manager"""
    try:
        notification_type = notification.get("type")
        download_id = notification.get("download_id")
        user_id = notification.get("user_id")
        data = notification.get("data", {})
        
        logger.info("Recebendo notificação do Celery", 
                   notification_type=notification_type,
                   download_id=download_id,
                   user_id=user_id)
        
        if notification_type == "download_update":
            await manager.send_download_update(download_id, data, user_id)
            logger.info("Notificação de download enviada via endpoint", 
                       download_id=download_id,
                       user_id=user_id)
        elif notification_type == "queue_update":
            await manager.send_queue_update(data)
            logger.info("Notificação de fila enviada via endpoint")
        elif notification_type == "stats_update":
            await manager.send_stats_update(data)
            logger.info("Notificação de estatísticas enviada via endpoint")
        elif notification_type == "dashboard_update":
            await manager.send_dashboard_update(data, user_id)
            logger.info("Notificação de dashboard enviada via endpoint", user_id=user_id)
        else:
            logger.warning("Tipo de notificação desconhecido", notification_type=notification_type)
            return {"error": "Tipo de notificação desconhecido"}
        
        return {"status": "success", "message": "Notificação enviada"}
        
    except Exception as e:
        logger.error("Erro ao processar notificação", error=str(e))
        return {"error": str(e)} 