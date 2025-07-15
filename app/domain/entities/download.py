from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

from app.domain.value_objects.download_status import DownloadStatus
from app.domain.value_objects.download_quality import DownloadQuality


class Download:
    """Entidade principal para representar um download de vídeo"""
    
    def __init__(
        self,
        url: str,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        duration: Optional[int] = None,
        thumbnail: Optional[str] = None,
        quality: DownloadQuality = DownloadQuality.BEST,
        id: Optional[UUID] = None,
        status: DownloadStatus = DownloadStatus.PENDING,
        progress: float = 0.0,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        format: Optional[str] = None,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        attempts: int = 0,
        error_message: Optional[str] = None,
        downloads_count: int = 0,
        last_accessed: Optional[datetime] = None,
        uploaded_to_drive: bool = False,
        drive_file_id: Optional[str] = None,
        storage_type: str = "temporary"
    ):
        self.id = id or uuid4()
        self.user_id = user_id
        self.url = url
        self.title = title
        self.description = description
        self.duration = duration
        self.thumbnail = thumbnail
        self.quality = quality
        self.status = status
        self.progress = progress
        self.file_path = file_path
        self.file_size = file_size
        self.format = format
        self.created_at = created_at or datetime.utcnow()
        self.started_at = started_at
        self.completed_at = completed_at
        self.attempts = attempts
        self.error_message = error_message
        self.downloads_count = downloads_count
        self.last_accessed = last_accessed
        self.uploaded_to_drive = uploaded_to_drive
        self.drive_file_id = drive_file_id
        self.storage_type = storage_type

    def start_download(self) -> None:
        """Inicia o download"""
        self.status = DownloadStatus.DOWNLOADING
        self.started_at = datetime.utcnow()
        self.attempts += 1

    def update_progress(self, progress: float) -> None:
        """Atualiza o progresso do download"""
        self.progress = max(0.0, min(100.0, progress))

    def complete_download(self, file_path: str, file_size: int, format: str) -> None:
        """Marca o download como concluído"""
        self.status = DownloadStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.utcnow()
        self.file_path = file_path
        self.file_size = file_size
        self.format = format

    def fail_download(self, error_message: str) -> None:
        """Marca o download como falhado"""
        self.status = DownloadStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def mark_as_uploaded_to_drive(self, drive_file_id: str) -> None:
        """Marca como enviado para o Google Drive"""
        self.uploaded_to_drive = True
        self.drive_file_id = drive_file_id

    def increment_download_count(self) -> None:
        """Incrementa o contador de downloads"""
        self.downloads_count += 1
        self.last_accessed = datetime.utcnow()

    def can_retry(self) -> bool:
        """Verifica se o download pode ser tentado novamente"""
        return self.status in [DownloadStatus.FAILED, DownloadStatus.CANCELLED]

    def is_expired(self, expiration_hours: int = 24) -> bool:
        """Verifica se o download expirou"""
        if not self.completed_at:
            return False
        
        expiration_time = self.completed_at.replace(
            hour=self.completed_at.hour + expiration_hours
        )
        return datetime.utcnow() > expiration_time

    @property
    def download_count(self) -> int:
        """Propriedade para compatibilidade com o modelo"""
        return self.downloads_count

    def to_dict(self) -> dict:
        """Converte a entidade para dicionário"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'thumbnail': self.thumbnail,
            'quality': self.quality.value,
            'status': self.status.value,
            'progress': self.progress,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'format': self.format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'attempts': self.attempts,
            'error_message': self.error_message,
            'downloads_count': self.downloads_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'uploaded_to_drive': self.uploaded_to_drive,
            'drive_file_id': self.drive_file_id,
            'storage_type': self.storage_type
        } 