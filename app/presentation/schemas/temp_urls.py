from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TemporaryURLCreateRequest(BaseModel):
    """Schema para criação de link temporário"""
    expiration_hours: int = Field(default=1, ge=1, le=24, description="Horas até expiração")
    max_accesses: Optional[int] = Field(default=None, ge=1, description="Máximo de acessos permitidos")
    custom_filename: Optional[str] = Field(default=None, max_length=255, description="Nome customizado do arquivo")


class TemporaryURLResponse(BaseModel):
    """Schema para resposta de link temporário"""
    id: UUID
    download_id: UUID
    temporary_url: str
    expiration_time: datetime
    access_count: int
    max_accesses: Optional[int] = None
    custom_filename: Optional[str] = None
    created_at: datetime
    is_expired: bool
    can_be_accessed: bool

    @classmethod
    def from_entity(cls, temp_file):
        """Cria response a partir da entidade"""
        return cls(
            id=temp_file.id,
            download_id=temp_file.download_id,
            temporary_url=temp_file.temporary_url,
            expiration_time=temp_file.expiration_time,
            access_count=temp_file.access_count,
            max_accesses=temp_file.max_accesses,
            custom_filename=temp_file.custom_filename,
            created_at=temp_file.created_at,
            is_expired=temp_file.is_expired(),
            can_be_accessed=temp_file.can_be_accessed()
        )


class TemporaryURLInfoResponse(BaseModel):
    """Schema para informações de link temporário"""
    download_id: str
    expiration_time: str
    access_count: int
    max_accesses: Optional[int] = None
    is_expired: bool
    is_access_limit_reached: bool
    file_exists: bool
    custom_filename: Optional[str] = None


class TemporaryURLExtendRequest(BaseModel):
    """Schema para extensão de link temporário"""
    additional_hours: int = Field(default=1, ge=1, le=24, description="Horas adicionais")


class TemporaryURLAccessLogResponse(BaseModel):
    """Schema para log de acesso de link temporário"""
    token: str
    created_at: str
    expiration_time: str
    access_count: int
    max_accesses: Optional[int] = None
    is_expired: bool


class TemporaryURLStatsResponse(BaseModel):
    """Schema para estatísticas de links temporários"""
    total_files: int
    active_files: int
    expired_files: int
    total_accesses: int 