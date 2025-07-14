from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID
from enum import Enum


class LogAction(str, Enum):
    """Ações que podem ser registradas no log"""
    DOWNLOAD_STARTED = "download_started"
    DOWNLOAD_PROGRESS = "download_progress"
    DOWNLOAD_COMPLETED = "download_completed"
    DOWNLOAD_FAILED = "download_failed"
    DOWNLOAD_CANCELLED = "download_cancelled"
    UPLOAD_TO_DRIVE = "upload_to_drive"
    CREATE_TEMP_URL = "create_temp_url"
    ACCESS_TEMP_URL = "access_temp_url"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    SYSTEM_ERROR = "system_error"


@dataclass
class DownloadLog:
    """Entidade para rastreamento detalhado de downloads"""
    
    id: Optional[UUID] = None
    download_id: Optional[UUID] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Informações do vídeo
    video_url: str = ""
    video_title: str = ""
    video_duration: Optional[int] = None
    video_size: Optional[int] = None
    video_format: str = ""
    video_quality: str = ""
    
    # Métricas de performance
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    download_duration: Optional[float] = None
    download_speed: Optional[float] = None
    file_size_downloaded: Optional[int] = None
    progress_percentage: Optional[float] = None
    
    # Status e resultado
    status: str = ""
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    
    # Informações do sistema
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_headers: Optional[Dict[str, Any]] = None
    response_headers: Optional[Dict[str, Any]] = None
    
    # Configurações de download
    download_path: Optional[str] = None
    output_format: Optional[str] = None
    quality_preference: Optional[str] = None
    
    # Integração com Google Drive
    google_drive_uploaded: bool = False
    google_drive_file_id: Optional[str] = None
    google_drive_folder_id: Optional[str] = None
    
    # URLs temporárias
    temporary_url_created: bool = False
    temporary_url_id: Optional[UUID] = None
    temporary_url_access_count: int = 0
    
    # Métricas de sistema
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def calculate_duration(self) -> Optional[float]:
        """Calcula a duração do download em segundos"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def calculate_speed(self) -> Optional[float]:
        """Calcula a velocidade média de download em MB/s"""
        if self.download_duration and self.file_size_downloaded:
            return self.file_size_downloaded / (1024 * 1024 * self.download_duration)
        return None
    
    def is_successful(self) -> bool:
        """Verifica se o download foi bem-sucedido"""
        return self.status == "completed" and self.error_message is None
    
    def has_error(self) -> bool:
        """Verifica se houve erro no download"""
        return self.error_message is not None or self.status in ["failed", "error"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade para dicionário"""
        return {
            "id": str(self.id) if self.id else None,
            "download_id": str(self.download_id) if self.download_id else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "video_url": self.video_url,
            "video_title": self.video_title,
            "video_duration": self.video_duration,
            "video_size": self.video_size,
            "video_format": self.video_format,
            "video_quality": self.video_quality,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "download_duration": self.download_duration,
            "download_speed": self.download_speed,
            "file_size_downloaded": self.file_size_downloaded,
            "progress_percentage": self.progress_percentage,
            "status": self.status,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "download_path": self.download_path,
            "output_format": self.output_format,
            "quality_preference": self.quality_preference,
            "google_drive_uploaded": self.google_drive_uploaded,
            "google_drive_file_id": self.google_drive_file_id,
            "google_drive_folder_id": self.google_drive_folder_id,
            "temporary_url_created": self.temporary_url_created,
            "temporary_url_id": str(self.temporary_url_id) if self.temporary_url_id else None,
            "temporary_url_access_count": self.temporary_url_access_count,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "disk_usage": self.disk_usage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 