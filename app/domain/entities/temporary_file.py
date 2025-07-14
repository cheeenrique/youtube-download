from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
import hashlib
import secrets


class TemporaryFile:
    """Entidade para representar um arquivo temporário com link de acesso"""
    
    def __init__(
        self,
        download_id: UUID,
        file_path: str,
        expiration_time: Optional[datetime] = None,
        access_count: int = 0,
        temporary_url: Optional[str] = None,
        file_hash: Optional[str] = None,
        max_accesses: Optional[int] = None,
        custom_filename: Optional[str] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        last_accessed: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.download_id = download_id
        self.file_path = file_path
        self.expiration_time = expiration_time or (datetime.utcnow() + timedelta(hours=1))
        self.access_count = access_count
        self.temporary_url = temporary_url
        self.file_hash = file_hash
        self.max_accesses = max_accesses
        self.custom_filename = custom_filename
        self.created_at = created_at or datetime.utcnow()
        self.last_accessed = last_accessed

    @property
    def url_hash(self) -> str:
        """Retorna o hash da URL temporária"""
        if self.temporary_url:
            return self.temporary_url.split('/')[-1]
        return ""

    def is_expired(self) -> bool:
        """Verifica se o arquivo temporário expirou"""
        return datetime.utcnow() > self.expiration_time

    def can_be_accessed(self) -> bool:
        """Verifica se o arquivo pode ser acessado"""
        if self.is_expired():
            return False
        
        if self.max_accesses and self.access_count >= self.max_accesses:
            return False
        
        return True

    def increment_access(self) -> bool:
        """Incrementa o contador de acesso e retorna se pode ser acessado"""
        if not self.can_be_accessed():
            return False
        
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        return True

    def extend_expiration(self, hours: int = 1) -> None:
        """Estende o tempo de expiração"""
        self.expiration_time = datetime.utcnow() + timedelta(hours=hours)

    def to_dict(self) -> dict:
        """Converte a entidade para dicionário"""
        return {
            'id': str(self.id),
            'download_id': str(self.download_id),
            'file_path': self.file_path,
            'temporary_url': self.temporary_url,
            'url_hash': self.url_hash,
            'expiration_time': self.expiration_time.isoformat() if self.expiration_time else None,
            'access_count': self.access_count,
            'max_accesses': self.max_accesses,
            'file_hash': self.file_hash,
            'custom_filename': self.custom_filename,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'is_expired': self.is_expired(),
            'can_be_accessed': self.can_be_accessed()
        } 