from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field

from app.domain.value_objects.download_quality import DownloadQuality
from app.domain.value_objects.download_status import DownloadStatus


class DownloadCreateRequest(BaseModel):
    """Schema para criação de download"""
    url: HttpUrl = Field(..., description="URL do vídeo para download")
    quality: DownloadQuality = Field(default=DownloadQuality.BEST, description="Qualidade do download")
    upload_to_drive: bool = Field(default=False, description="Se deve fazer upload para o Google Drive")


class DownloadBatchRequest(BaseModel):
    """Schema para criação de múltiplos downloads"""
    urls: List[HttpUrl] = Field(..., description="Lista de URLs para download", min_items=1, max_items=10)
    quality: DownloadQuality = Field(default=DownloadQuality.BEST, description="Qualidade dos downloads")
    upload_to_drive: bool = Field(default=False, description="Se deve fazer upload para o Google Drive")


class DownloadResponse(BaseModel):
    """Schema para resposta de download"""
    id: UUID
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    quality: str
    status: str
    progress: float
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int
    error_message: Optional[str] = None
    downloads_count: int
    last_accessed: Optional[datetime] = None
    uploaded_to_drive: bool
    drive_file_id: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, download):
        """Criar schema a partir da entidade Download"""
        return cls(
            id=download.id,
            url=download.url,
            title=download.title,
            description=download.description,
            duration=download.duration,
            thumbnail=download.thumbnail,
            quality=download.quality.value if download.quality else "best",
            status=download.status.value if download.status else "pending",
            progress=download.progress or 0.0,
            file_path=download.file_path,
            file_size=download.file_size,
            format=download.format,
            created_at=download.created_at,
            started_at=download.started_at,
            completed_at=download.completed_at,
            attempts=download.attempts or 0,
            error_message=download.error_message,
            downloads_count=download.downloads_count or 0,
            last_accessed=download.last_accessed,
            uploaded_to_drive=download.uploaded_to_drive or False,
            drive_file_id=download.drive_file_id
        )


class DownloadStatusResponse(BaseModel):
    """Schema para resposta de status de download"""
    id: UUID
    status: str
    progress: float
    error_message: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # em segundos


class DownloadQueueResponse(BaseModel):
    """Schema para resposta da fila de downloads"""
    pending: int
    downloading: int
    completed: int
    failed: int
    total: int
    queue_position: Optional[int] = None  # para downloads específicos


class DownloadStatsResponse(BaseModel):
    """Schema para resposta de estatísticas"""
    total_downloads: int
    completed_downloads: int
    failed_downloads: int
    pending_downloads: int
    downloads_today: int
    downloads_this_week: int
    downloads_this_month: int
    total_storage_used: int  # em bytes
    average_download_time: float  # em segundos


class TemporaryFileResponse(BaseModel):
    """Schema para resposta de arquivo temporário"""
    id: UUID
    download_id: UUID
    temporary_url: str
    expiration_time: datetime
    access_count: int
    max_access_count: Optional[int] = None
    created_at: datetime
    last_accessed: Optional[datetime] = None
    is_expired: bool
    can_be_accessed: bool

    class Config:
        from_attributes = True


class DownloadListResponse(BaseModel):
    """Schema para resposta de lista de downloads"""
    downloads: List[DownloadResponse]
    total: int
    limit: int
    offset: int

    class Config:
        from_attributes = True 