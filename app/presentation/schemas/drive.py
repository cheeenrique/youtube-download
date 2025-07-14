from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


class DriveConfigCreateRequest(BaseModel):
    """Schema para criação de configuração do Google Drive"""
    user_id: str = Field(..., description="ID do usuário")
    credentials: Dict[str, Any] = Field(..., description="Credenciais do Google Drive")
    folder_id: Optional[str] = Field(None, description="ID da pasta do Google Drive")
    custom_key: Optional[str] = Field(None, description="Chave customizada")
    is_default: bool = Field(default=False, description="Se é a configuração padrão")


class DriveConfigUpdateRequest(BaseModel):
    """Schema para atualização de configuração do Google Drive"""
    folder_id: Optional[str] = Field(None, description="ID da pasta do Google Drive")
    custom_key: Optional[str] = Field(None, description="Chave customizada")
    is_default: Optional[bool] = Field(None, description="Se é a configuração padrão")


class DriveConfigResponse(BaseModel):
    """Schema para resposta de configuração do Google Drive"""
    id: UUID
    user_id: str
    folder_id: Optional[str] = None
    custom_key: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    quota_used: int
    quota_limit: Optional[int] = None
    quota_percentage: float
    is_default: bool
    is_valid: bool

    @classmethod
    def from_entity(cls, config):
        """Cria response a partir da entidade"""
        return cls(
            id=config.id,
            user_id=config.user_id,
            folder_id=config.folder_id,
            custom_key=config.custom_key,
            status=config.status.value,
            created_at=config.created_at,
            updated_at=config.updated_at,
            last_sync=config.last_sync,
            error_message=config.error_message,
            quota_used=config.quota_used,
            quota_limit=config.quota_limit,
            quota_percentage=config.get_quota_percentage(),
            is_default=config.is_default,
            is_valid=config.is_valid()
        )

    class Config:
        from_attributes = True


class DriveConfigListResponse(BaseModel):
    """Schema para lista de configurações do Google Drive"""
    configs: List[DriveConfigResponse]
    total: int


class DriveFolderResponse(BaseModel):
    """Schema para resposta de pasta do Google Drive"""
    id: str
    name: str
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    parents: Optional[List[str]] = None

    @classmethod
    def from_drive_folder(cls, folder):
        """Cria response a partir da pasta do Google Drive"""
        return cls(
            id=folder['id'],
            name=folder['name'],
            created_time=folder.get('createdTime'),
            modified_time=folder.get('modifiedTime'),
            parents=folder.get('parents')
        )


class DriveUploadRequest(BaseModel):
    """Schema para request de upload para Google Drive"""
    config_id: Optional[str] = None
    folder_id: Optional[str] = None


class DriveQuotaResponse(BaseModel):
    """Schema para resposta de quota do Google Drive"""
    used: int
    limit: int
    percentage: float


class DriveTestResponse(BaseModel):
    """Schema para resposta de teste de conexão"""
    message: str


class DriveUploadResponse(BaseModel):
    """Schema para resposta de upload para o Google Drive"""
    download_id: UUID
    drive_file_id: str
    drive_file_name: str
    drive_file_size: int
    drive_file_url: str
    uploaded_at: datetime
    status: str 