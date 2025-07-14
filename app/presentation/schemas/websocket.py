from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """Schema base para mensagens WebSocket"""
    type: str = Field(..., description="Tipo da mensagem")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da mensagem")


class ConnectionEstablishedMessage(WebSocketMessage):
    """Mensagem de conexão estabelecida"""
    type: str = Field(default="connection_established", description="Tipo da mensagem")
    message: str = Field(..., description="Mensagem de confirmação")
    download_id: Optional[str] = Field(None, description="ID do download (se aplicável)")


class DownloadUpdateMessage(WebSocketMessage):
    """Mensagem de atualização de download"""
    type: str = Field(default="download_update", description="Tipo da mensagem")
    download_id: str = Field(..., description="ID do download")
    progress: float = Field(..., description="Progresso do download (0-100)")
    status: str = Field(..., description="Status do download")
    error_message: Optional[str] = Field(None, description="Mensagem de erro (se houver)")
    file_path: Optional[str] = Field(None, description="Caminho do arquivo (se concluído)")
    completed_at: Optional[datetime] = Field(None, description="Data de conclusão")
    failed_at: Optional[datetime] = Field(None, description="Data de falha")


class QueueUpdateMessage(WebSocketMessage):
    """Mensagem de atualização da fila"""
    type: str = Field(default="queue_update", description="Tipo da mensagem")
    pending: int = Field(..., description="Downloads pendentes")
    downloading: int = Field(..., description="Downloads em andamento")
    completed: int = Field(..., description="Downloads concluídos")
    failed: int = Field(..., description="Downloads falhados")
    total: int = Field(..., description="Total de downloads")
    queue_position: Optional[int] = Field(None, description="Posição na fila")


class StatsUpdateMessage(WebSocketMessage):
    """Mensagem de atualização de estatísticas"""
    type: str = Field(default="stats_update", description="Tipo da mensagem")
    total_downloads: int = Field(..., description="Total de downloads")
    completed_downloads: int = Field(..., description="Downloads concluídos")
    failed_downloads: int = Field(..., description="Downloads falhados")
    pending_downloads: int = Field(..., description="Downloads pendentes")
    downloads_today: int = Field(..., description="Downloads hoje")
    downloads_this_week: int = Field(..., description="Downloads esta semana")
    downloads_this_month: int = Field(..., description="Downloads este mês")
    total_storage_used: int = Field(..., description="Storage usado em bytes")
    average_download_time: float = Field(..., description="Tempo médio de download em segundos")


class ErrorMessage(WebSocketMessage):
    """Mensagem de erro"""
    type: str = Field(default="error", description="Tipo da mensagem")
    error: str = Field(..., description="Mensagem de erro")
    download_id: Optional[str] = Field(None, description="ID do download (se aplicável)")


class PingMessage(BaseModel):
    """Mensagem de ping"""
    type: str = Field(default="ping", description="Tipo da mensagem")
    timestamp: Optional[datetime] = Field(None, description="Timestamp do ping")


class PongMessage(BaseModel):
    """Mensagem de pong"""
    type: str = Field(default="pong", description="Tipo da mensagem")
    timestamp: Optional[datetime] = Field(None, description="Timestamp do pong")


class ConnectionCountResponse(BaseModel):
    """Resposta com contagem de conexões"""
    download_connections: int = Field(..., description="Conexões de download")
    queue_connections: int = Field(..., description="Conexões da fila")
    stats_connections: int = Field(..., description="Conexões de estatísticas")
    general_connections: int = Field(..., description="Conexões gerais")
    total: int = Field(..., description="Total de conexões")


# Schemas para SSE (Server-Sent Events)
class SSEEvent(BaseModel):
    """Schema base para eventos SSE"""
    type: str = Field(..., description="Tipo do evento")
    data: Dict[str, Any] = Field(..., description="Dados do evento")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do evento")


class DownloadProgressEvent(SSEEvent):
    """Evento de progresso de download via SSE"""
    type: str = Field(default="progress_update", description="Tipo do evento")
    data: DownloadUpdateMessage = Field(..., description="Dados do progresso")


class QueueStatusEvent(SSEEvent):
    """Evento de status da fila via SSE"""
    type: str = Field(default="queue_update", description="Tipo do evento")
    data: QueueUpdateMessage = Field(..., description="Dados da fila")


class StatsEvent(SSEEvent):
    """Evento de estatísticas via SSE"""
    type: str = Field(default="stats_update", description="Tipo do evento")
    data: StatsUpdateMessage = Field(..., description="Dados das estatísticas") 