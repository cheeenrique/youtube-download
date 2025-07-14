from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.domain.entities.download import Download
from app.domain.value_objects.download_status import DownloadStatus


class DownloadRepository(ABC):
    """Interface para o repositório de downloads"""
    
    @abstractmethod
    async def create(self, download: Download) -> Download:
        """Cria um novo download"""
        pass
    
    @abstractmethod
    async def get_by_id(self, download_id: UUID) -> Optional[Download]:
        """Busca um download por ID"""
        pass
    
    @abstractmethod
    async def get_by_url(self, url: str) -> Optional[Download]:
        """Busca um download por URL"""
        pass
    
    @abstractmethod
    async def update(self, download: Download) -> Download:
        """Atualiza um download"""
        pass
    
    @abstractmethod
    async def delete(self, download_id: UUID) -> bool:
        """Deleta um download"""
        pass
    
    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista todos os downloads"""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: DownloadStatus, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads por status"""
        pass
    
    @abstractmethod
    async def list_pending_downloads(self, limit: int = 10) -> List[Download]:
        """Lista downloads pendentes para processamento"""
        pass
    
    @abstractmethod
    async def list_failed_downloads(self, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads que falharam"""
        pass
    
    @abstractmethod
    async def list_completed_downloads(self, limit: int = 100, offset: int = 0) -> List[Download]:
        """Lista downloads concluídos"""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: DownloadStatus) -> int:
        """Conta downloads por status"""
        pass
    
    @abstractmethod
    async def get_download_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos downloads"""
        pass
    
    @abstractmethod
    async def cleanup_expired_downloads(self, expiration_hours: int = 24) -> int:
        """Remove downloads expirados e retorna a quantidade removida"""
        pass
    
    @abstractmethod
    async def search_downloads(self, query: str, limit: int = 100, offset: int = 0) -> List[Download]:
        """Busca downloads por título ou descrição"""
        pass 