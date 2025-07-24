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
        # Conexões do dashboard completo por usuário
        self.dashboard_connections: Dict[str, Set[WebSocket]] = {}
        # Mapeamento de WebSocket para usuário
        self.websocket_users: Dict[WebSocket, str] = {}
    
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
    
    async def connect_dashboard(self, websocket: WebSocket, user_id: str):
        """Conecta um WebSocket para dashboard completo"""
        # Não aceitar novamente - já foi aceito na autenticação
        
        if user_id not in self.dashboard_connections:
            self.dashboard_connections[user_id] = set()
        
        self.dashboard_connections[user_id].add(websocket)
        self.websocket_users[websocket] = user_id
        logger.info("WebSocket conectado para dashboard", user_id=user_id)
    
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
        user_id = self.websocket_users.get(websocket)
        if user_id and user_id in self.dashboard_connections:
            self.dashboard_connections[user_id].discard(websocket)
            if not self.dashboard_connections[user_id]:
                del self.dashboard_connections[user_id]
        
        # Remover do mapeamento
        self.websocket_users.pop(websocket, None)
        logger.info("WebSocket desconectado do dashboard", user_id=user_id)
    
    async def disconnect_user(self, user_id: str):
        """Desconecta todas as conexões de um usuário específico"""
        if user_id in self.dashboard_connections:
            connections_to_close = self.dashboard_connections[user_id].copy()
            for websocket in connections_to_close:
                try:
                    await websocket.close(code=1000, reason="User logout")
                except Exception as e:
                    logger.error("Erro ao fechar WebSocket do usuário", error=str(e), user_id=user_id)
            
            # Limpar do mapeamento
            for websocket in connections_to_close:
                self.websocket_users.pop(websocket, None)
            
            # Remover do dicionário
            del self.dashboard_connections[user_id]
            logger.info("Todas as conexões do usuário desconectadas", user_id=user_id, count=len(connections_to_close))
    
    async def clear_all_connections(self):
        """Limpa todas as conexões WebSocket ativas"""
        # Fechar todas as conexões do dashboard
        for user_id, connections in self.dashboard_connections.items():
            for websocket in connections:
                try:
                    await websocket.close(code=1000, reason="Server cleanup")
                except Exception as e:
                    logger.error("Erro ao fechar WebSocket durante limpeza", error=str(e))
        
        # Fechar todas as outras conexões
        for websocket in self.general_connections:
            try:
                await websocket.close(code=1000, reason="Server cleanup")
            except Exception as e:
                logger.error("Erro ao fechar WebSocket geral durante limpeza", error=str(e))
        
        for websocket in self.queue_connections:
            try:
                await websocket.close(code=1000, reason="Server cleanup")
            except Exception as e:
                logger.error("Erro ao fechar WebSocket da fila durante limpeza", error=str(e))
        
        for websocket in self.stats_connections:
            try:
                await websocket.close(code=1000, reason="Server cleanup")
            except Exception as e:
                logger.error("Erro ao fechar WebSocket de estatísticas durante limpeza", error=str(e))
        
        for download_id, connections in self.download_connections.items():
            for websocket in connections:
                try:
                    await websocket.close(code=1000, reason="Server cleanup")
                except Exception as e:
                    logger.error("Erro ao fechar WebSocket de download durante limpeza", error=str(e), download_id=download_id)
        
        # Limpar todas as estruturas de dados
        self.download_connections.clear()
        self.general_connections.clear()
        self.queue_connections.clear()
        self.stats_connections.clear()
        self.dashboard_connections.clear()
        self.websocket_users.clear()
        
        logger.info("Todas as conexões WebSocket foram limpas")
    
    async def send_download_update(self, download_id: str, data: Dict[str, Any], user_id: str = None):
        """Envia atualização para um download específico e dashboard do usuário"""
        message = {
            "type": "download_update",
            "download_id": str(download_id),
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"🔍 [WebSocket Manager] Enviando notificação de download")
        print(f"    - download_id: {download_id}")
        print(f"    - user_id: {user_id}")
        print(f"    - message_type: {message['type']}")
        print(f"    - message_content: {message}")
        
        logger.info("Enviando notificação de download", 
                   download_id=download_id, 
                   user_id=user_id,
                   message_type=message["type"],
                   message_content=message)
        
        # Enviar para conexões específicas do download
        if download_id in self.download_connections:
            logger.info("Enviando para conexões específicas do download", 
                       download_id=download_id,
                       connection_count=len(self.download_connections[download_id]))
            disconnected = set()
            for connection in self.download_connections[download_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.info("Mensagem enviada para conexão específica", download_id=download_id)
                except WebSocketDisconnect:
                    disconnected.add(connection)
                    logger.warning("Conexão específica desconectada", download_id=download_id)
                except Exception as e:
                    logger.error("Erro ao enviar mensagem WebSocket", error=str(e))
                    disconnected.add(connection)
            
            # Remove conexões desconectadas
            for connection in disconnected:
                await self.disconnect_download(connection, download_id)
        else:
            logger.info("Nenhuma conexão específica para o download", download_id=download_id)
        
        # Enviar para conexões do dashboard do usuário específico
        print(f"🔍 [WebSocket Manager] Verificando conexões do dashboard")
        print(f"    - user_id: {user_id}")
        print(f"    - dashboard_connections keys: {list(self.dashboard_connections.keys())}")
        print(f"    - user_id in dashboard_connections: {user_id in self.dashboard_connections}")
        
        if user_id and user_id in self.dashboard_connections:
            connection_count = len(self.dashboard_connections[user_id])
            print(f"🔍 [WebSocket Manager] Enviando para {connection_count} conexões do dashboard")
            logger.info("Enviando para conexões do dashboard", 
                       user_id=user_id,
                       connection_count=connection_count)
            disconnected = set()
            for connection in self.dashboard_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                    logger.info("Mensagem enviada para conexão do dashboard", user_id=user_id)
                except WebSocketDisconnect:
                    disconnected.add(connection)
                    logger.warning("Conexão do dashboard desconectada", user_id=user_id)
                except Exception as e:
                    logger.error("Erro ao enviar mensagem WebSocket do dashboard", error=str(e))
                    disconnected.add(connection)
            
            # Remove conexões desconectadas
            for connection in disconnected:
                await self.disconnect_dashboard(connection)
        else:
            logger.warning("Nenhuma conexão do dashboard encontrada", 
                          user_id=user_id, 
                          dashboard_connections_keys=list(self.dashboard_connections.keys()),
                          dashboard_connections_count=len(self.dashboard_connections),
                          all_user_ids=list(self.dashboard_connections.keys()))
        
        logger.info("Notificação de download enviada", 
                   download_id=download_id, 
                   user_id=user_id)
    
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
    
    async def send_dashboard_update(self, data: Dict[str, Any], user_id: str = None):
        """Envia atualização completa do dashboard para usuário específico"""
        message = {
            "type": "dashboard_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if user_id and user_id in self.dashboard_connections:
            disconnected = set()
            for connection in self.dashboard_connections[user_id]:
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
        dashboard_total = sum(len(connections) for connections in self.dashboard_connections.values())
        return {
            "download_connections": sum(len(connections) for connections in self.download_connections.values()),
            "queue_connections": len(self.queue_connections),
            "stats_connections": len(self.stats_connections),
            "general_connections": len(self.general_connections),
            "dashboard_connections": dashboard_total,
            "total": sum(len(connections) for connections in self.download_connections.values()) + 
                    len(self.queue_connections) + 
                    len(self.stats_connections) + 
                    len(self.general_connections) +
                    dashboard_total
        }


# Instância global do manager
manager = ConnectionManager() 