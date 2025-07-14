from enum import Enum


class DownloadStatus(Enum):
    """Status possíveis para um download"""
    
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UPLOADING_TO_DRIVE = "uploading_to_drive"
    UPLOADED_TO_DRIVE = "uploaded_to_drive"
    EXPIRED = "expired" 