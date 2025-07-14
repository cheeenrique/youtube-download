from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import structlog
from datetime import datetime
from uuid import UUID

logger = structlog.get_logger()


class ConnectionManager:
    """Gerenciador de conexões WebSocket para tempo real"""
    
    def __init__(self):
        # Conexões ativas por download_id
        self.download_connections: Dict[str, Set[WebSocket]] = {}
        # Conexões gerais (para fila e estatísticas)
        self.general_connections: Set[WebSocket] = set()
        # Conexões por tipo
        self.queue_connections: Set[WebSocket] = set()
        self.stats_connections: Set[WebSocket] = set()
        # Conexões do dashboard completo
        self.dashboard_connections: Set[WebSocket] = set()
    
    async def connect_download(self, websocket: WebSocket, download_id: str):
        """Conecta um WebSocket para um download específico"""
        await websocket.accept()
        
        if download_id not in self.download_connections:
            self.download_connections[download_id] = set()
        
        self.download_connections[download_id].add(websocket)
        logger.info("WebSocket conectado para download", download_id=download_id)
    
    async def connect_queue(self, websocket: WebSocket):
        """Conecta um WebSocket para monitoramento da fila"""
        await websocket.accept()
        self.queue_connections.add(websocket)
        logger.info("WebSocket conectado para fila")
    
    async def connect_stats(self, websocket: WebSocket):
        """Conecta um WebSocket para estatísticas"""
        await websocket.accept()
        self.stats_connections.add(websocket)
        logger.info("WebSocket conectado para estatísticas")
    
    async def connect_general(self, websocket: WebSocket):
        """Conecta um WebSocket para mensagens gerais"""
        await websocket.accept()
        self.general_connections.add(websocket)
        logger.info("WebSocket conectado para mensagens gerais")
    
    async def connect_dashboard(self, websocket: WebSocket):
        """Conecta um WebSocket para dashboard completo"""
        await websocket.accept()
        self.dashboard_connections.add(websocket)
        logger.info("WebSocket conectado para dashboard")
    
    async def disconnect_download(self, websocket: WebSocket, download_id: str):
        """Desconecta um WebSocket de um download específico"""
        if download_id in self.download_connections:
            self.download_connections[download_id].discard(websocket)
            if not self.download_connections[download_id]:
                del self.download_connections[download_id]
        logger.info("WebSocket desconectado do download", download_id=download_id)
    
    async def disconnect_queue(self, websocket: WebSocket):
        """Desconecta um WebSocket da fila"""
        self.queue_connections.discard(websocket)
        logger.info("WebSocket desconectado da fila")
    
    async def disconnect_stats(self, websocket: WebSocket):
        """Desconecta um WebSocket das estatísticas"""
        self.stats_connections.discard(websocket)
        logger.info("WebSocket desconectado das estatísticas")
    
    async def disconnect_general(self, websocket: WebSocket):
        """Desconecta um WebSocket geral"""
        self.general_connections.discard(websocket)
        logger.info("WebSocket desconectado das mensagens gerais")
    
    async def disconnect_dashboard(self, websocket: WebSocket):
        """Desconecta um WebSocket do dashboard"""
        self.dashboard_connections.discard(websocket)
        logger.info("WebSocket desconectado do dashboard")
    
    async def send_download_update(self, download_id: str, data: Dict[str, Any]):
        """Envia atualização para um download específico"""
        if download_id not in self.download_connections:
            return
        
        message = {
            "type": "download_update",
            "download_id": str(download_id),
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.download_connections[download_id]:
            try:
                await connection.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error("Erro ao enviar mensagem WebSocket", error=str(e))
                disconnected.add(connection)
        
        # Remove conexões desconectadas
        for connection in disconnected:
            await self.disconnect_download(connection, download_id)
    
    async def send_queue_update(self, data: Dict[str, Any]):
        """Envia atualização da fila"""
        message = {
            "type": "queue_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.queue_connections:
            try:
                await connection.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error("Erro ao enviar mensagem WebSocket", error=str(e))
                disconnected.add(connection)
        
        # Remove conexões desconectadas
        for connection in disconnected:
            await self.disconnect_queue(connection)
    
    async def send_stats_update(self, data: Dict[str, Any]):
        """Envia atualização de estatísticas"""
        message = {
            "type": "stats_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.stats_connections:
            try:
                await connection.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error("Erro ao enviar mensagem WebSocket", error=str(e))
                disconnected.add(connection)
        
        # Remove conexões desconectadas
        for connection in disconnected:
            await self.disconnect_stats(connection)
    
    async def send_general_message(self, message_type: str, data: Dict[str, Any]):
        """Envia mensagem geral"""
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.general_connections:
            try:
                await connection.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error("Erro ao enviar mensagem WebSocket", error=str(e))
                disconnected.add(connection)
        
        # Remove conexões desconectadas
        for connection in disconnected:
            await self.disconnect_general(connection)
    
    async def send_dashboard_update(self, data: Dict[str, Any]):
        """Envia atualização completa do dashboard"""
        message = {
            "type": "dashboard_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = set()
        for connection in self.dashboard_connections:
            try:
                await connection.send_text(json.dumps(message))
            except WebSocketDisconnect:
                disconnected.add(connection)
            except Exception as e:
                logger.error("Erro ao enviar mensagem WebSocket do dashboard", error=str(e))
                disconnected.add(connection)
        
        # Remove conexões desconectadas
        for connection in disconnected:
            await self.disconnect_dashboard(connection)
    
    def get_connection_count(self) -> Dict[str, int]:
        """Retorna contagem de conexões ativas"""
        return {
            "download_connections": sum(len(connections) for connections in self.download_connections.values()),
            "queue_connections": len(self.queue_connections),
            "stats_connections": len(self.stats_connections),
            "general_connections": len(self.general_connections),
            "dashboard_connections": len(self.dashboard_connections),
            "total": sum(len(connections) for connections in self.download_connections.values()) + 
                    len(self.queue_connections) + 
                    len(self.stats_connections) + 
                    len(self.general_connections) +
                    len(self.dashboard_connections)
        }


# Instância global do manager
manager = ConnectionManager() 