from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum


class DriveConfigStatus(Enum):
    """Status da configuração do Google Drive"""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"


class GoogleDriveConfig:
    """Entidade para representar configurações do Google Drive"""
    
    def __init__(
        self,
        user_id: str,
        credentials: Dict[str, Any],
        folder_id: Optional[str] = None,
        custom_key: Optional[str] = None,
        status: DriveConfigStatus = DriveConfigStatus.INACTIVE,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        last_sync: Optional[datetime] = None,
        error_message: Optional[str] = None,
        quota_used: int = 0,
        quota_limit: Optional[int] = None,
        is_default: bool = False
    ):
        self.id = id or uuid4()
        self.user_id = user_id
        self.credentials = credentials
        self.folder_id = folder_id
        self.custom_key = custom_key
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.last_sync = last_sync
        self.error_message = error_message
        self.quota_used = quota_used
        self.quota_limit = quota_limit
        self.is_default = is_default

    def activate(self) -> None:
        """Ativa a configuração"""
        self.status = DriveConfigStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        self.error_message = None

    def deactivate(self) -> None:
        """Desativa a configuração"""
        self.status = DriveConfigStatus.INACTIVE
        self.updated_at = datetime.utcnow()

    def mark_as_error(self, error_message: str) -> None:
        """Marca a configuração como com erro"""
        self.status = DriveConfigStatus.ERROR
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def start_sync(self) -> None:
        """Inicia o processo de sincronização"""
        self.status = DriveConfigStatus.SYNCING
        self.updated_at = datetime.utcnow()

    def complete_sync(self) -> None:
        """Finaliza o processo de sincronização"""
        self.status = DriveConfigStatus.ACTIVE
        self.last_sync = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_quota(self, used: int, limit: Optional[int] = None) -> None:
        """Atualiza informações de quota"""
        self.quota_used = used
        if limit:
            self.quota_limit = limit
        self.updated_at = datetime.utcnow()

    def has_quota_available(self, required_space: int = 0) -> bool:
        """Verifica se há quota disponível"""
        if not self.quota_limit:
            return True
        
        return (self.quota_used + required_space) <= self.quota_limit

    def get_quota_percentage(self) -> float:
        """Retorna a porcentagem de quota utilizada"""
        if not self.quota_limit:
            return 0.0
        
        return (self.quota_used / self.quota_limit) * 100

    def is_valid(self) -> bool:
        """Verifica se a configuração é válida"""
        return (
            self.status == DriveConfigStatus.ACTIVE and
            self.credentials is not None and
            len(self.credentials) > 0
        )

    def to_dict(self) -> dict:
        """Converte a entidade para dicionário"""
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'folder_id': self.folder_id,
            'custom_key': self.custom_key,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'error_message': self.error_message,
            'quota_used': self.quota_used,
            'quota_limit': self.quota_limit,
            'quota_percentage': self.get_quota_percentage(),
            'is_default': self.is_default,
            'is_valid': self.is_valid()
        } 