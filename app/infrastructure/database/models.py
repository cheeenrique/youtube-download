from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
from typing import Dict, Any
from sqlalchemy import JSON, BigInteger

Base = declarative_base()


class DownloadModel(Base):
    """Modelo SQLAlchemy para Download"""
    __tablename__ = "downloads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    url = Column(String(500), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    progress = Column(Float, default=0.0)
    title = Column(String(500))
    description = Column(Text)
    duration = Column(Integer)  # em segundos
    thumbnail = Column(String(500))
    quality = Column(String(50))
    format = Column(String(50))
    file_size = Column(Integer)  # em bytes
    file_path = Column(String(500))
    error_message = Column(Text)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    download_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)
    storage_type = Column(String(20), default="temporary", index=True)
    
    # Relacionamentos
    user = relationship("UserModel", back_populates="downloads")
    temporary_files = relationship("TemporaryFileModel", back_populates="download", cascade="all, delete-orphan")
    logs = relationship("DownloadLog", back_populates="download", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_downloads_status_created', 'status', 'created_at'),
        Index('idx_downloads_url_status', 'url', 'status'),
        Index('idx_downloads_user_status', 'user_id', 'status'),
    )


class TemporaryFileModel(Base):
    """Modelo SQLAlchemy para TemporaryFile"""
    __tablename__ = "temporary_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    download_id = Column(UUID(as_uuid=True), ForeignKey("downloads.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    expiration_time = Column(DateTime, nullable=False, index=True)
    access_count = Column(Integer, default=0)
    temporary_url = Column(String(500), unique=True, index=True)
    file_hash = Column(String(64), index=True)
    max_accesses = Column(Integer)
    custom_filename = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    download = relationship("DownloadModel", back_populates="temporary_files")
    download_logs = relationship("DownloadLog", back_populates="temporary_file")
    
    # Índices
    __table_args__ = (
        Index('idx_temp_files_expiration', 'expiration_time'),
        Index('idx_temp_files_download_hash', 'download_id', 'file_hash'),
        Index('idx_temp_files_url', 'temporary_url'),
    )


class GoogleDriveConfigModel(Base):
    """Modelo SQLAlchemy para GoogleDriveConfig"""
    __tablename__ = "google_drive_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_name = Column(String(100), nullable=False, unique=True)
    credentials_file = Column(String(500), nullable=False)
    folder_id = Column(String(100))
    is_active = Column(Boolean, default=True)
    quota_used = Column(Integer, default=0)  # em bytes
    quota_limit = Column(Integer)  # em bytes
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Índices
    __table_args__ = (
        Index('idx_drive_config_active', 'is_active'),
        Index('idx_drive_config_account', 'account_name'),
    )


class DownloadLog(Base):
    """Modelo SQLAlchemy para logs de download"""
    
    __tablename__ = "download_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    download_id = Column(UUID(as_uuid=True), ForeignKey("downloads.id"), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Informações do vídeo
    video_url = Column(Text, nullable=False)
    video_title = Column(String(500), nullable=False)
    video_duration = Column(Integer, nullable=True)
    video_size = Column(BigInteger, nullable=True)
    video_format = Column(String(50), nullable=False)
    video_quality = Column(String(50), nullable=False)
    
    # Métricas de performance
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    download_duration = Column(Float, nullable=True)
    download_speed = Column(Float, nullable=True)
    file_size_downloaded = Column(BigInteger, nullable=True)
    progress_percentage = Column(Float, nullable=True)
    
    # Status e resultado
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Informações do sistema
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_headers = Column(JSON, nullable=True)
    response_headers = Column(JSON, nullable=True)
    
    # Configurações de download
    download_path = Column(String(500), nullable=True)
    output_format = Column(String(50), nullable=True)
    quality_preference = Column(String(50), nullable=True)
    
    # Integração com Google Drive
    google_drive_uploaded = Column(Boolean, default=False)
    google_drive_file_id = Column(String(255), nullable=True)
    google_drive_folder_id = Column(String(255), nullable=True)
    
    # URLs temporárias
    temporary_url_created = Column(Boolean, default=False)
    temporary_url_id = Column(UUID(as_uuid=True), ForeignKey("temporary_files.id"), nullable=True)
    temporary_url_access_count = Column(Integer, default=0)
    
    # Métricas de sistema
    memory_usage = Column(Float, nullable=True)
    cpu_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relacionamentos
    download = relationship("DownloadModel", back_populates="logs")
    temporary_file = relationship("TemporaryFileModel", back_populates="download_logs")
    
    def __repr__(self):
        return f"<DownloadLog(id={self.id}, download_id={self.download_id}, status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário"""
        return {
            "id": str(self.id),
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
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
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


class UserModel(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    salt = Column(String(64), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    downloads = relationship("DownloadModel", back_populates="user", cascade="all, delete-orphan") 