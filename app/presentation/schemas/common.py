from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Tipo genérico para respostas paginadas
T = TypeVar('T')


class PaginationParams(BaseModel):
    """Parâmetros de paginação"""
    page: int = Field(default=1, ge=1, description="Número da página")
    size: int = Field(default=10, ge=1, le=100, description="Tamanho da página")
    sort_by: Optional[str] = Field(default=None, description="Campo para ordenação")
    sort_order: Optional[str] = Field(default="asc", description="Ordem da ordenação (asc/desc)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Resposta paginada genérica"""
    items: List[T] = Field(description="Lista de itens")
    total: int = Field(description="Total de itens")
    page: int = Field(description="Página atual")
    size: int = Field(description="Tamanho da página")
    pages: int = Field(description="Total de páginas")
    has_next: bool = Field(description="Se há próxima página")
    has_prev: bool = Field(description="Se há página anterior")


class ErrorResponse(BaseModel):
    """Resposta de erro padrão"""
    error: str = Field(description="Mensagem de erro")
    code: Optional[str] = Field(default=None, description="Código do erro")
    details: Optional[dict] = Field(default=None, description="Detalhes do erro")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do erro")


class SuccessResponse(BaseModel):
    """Resposta de sucesso padrão"""
    message: str = Field(description="Mensagem de sucesso")
    data: Optional[Any] = Field(default=None, description="Dados da resposta")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da resposta")


class HealthCheckResponse(BaseModel):
    """Resposta de health check"""
    status: str = Field(description="Status do serviço")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do check")
    version: Optional[str] = Field(default=None, description="Versão da aplicação")
    uptime: Optional[float] = Field(default=None, description="Tempo de atividade em segundos")


class StatusResponse(BaseModel):
    """Resposta de status genérica"""
    status: str = Field(description="Status da operação")
    message: Optional[str] = Field(default=None, description="Mensagem adicional")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da resposta")


class CountResponse(BaseModel):
    """Resposta com contagem"""
    count: int = Field(description="Número de itens")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da resposta")


class ListResponse(BaseModel, Generic[T]):
    """Resposta de lista simples"""
    items: List[T] = Field(description="Lista de itens")
    count: int = Field(description="Número de itens")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da resposta") 