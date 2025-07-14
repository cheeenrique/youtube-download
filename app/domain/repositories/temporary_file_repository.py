from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from app.domain.entities.temporary_file import TemporaryFile


class TemporaryFileRepository(ABC):
    """Interface para o repositório de arquivos temporários"""
    
    @abstractmethod
    async def create(self, temporary_file: TemporaryFile) -> TemporaryFile:
        """Cria um novo arquivo temporário"""
        pass
    
    @abstractmethod
    async def get_by_id(self, file_id: UUID) -> Optional[TemporaryFile]:
        """Busca um arquivo temporário por ID"""
        pass
    
    @abstractmethod
    async def get_by_download_id(self, download_id: UUID) -> Optional[TemporaryFile]:
        """Busca um arquivo temporário por download ID"""
        pass
    
    @abstractmethod
    async def get_by_url_hash(self, url_hash: str) -> Optional[TemporaryFile]:
        """Busca um arquivo temporário por hash da URL"""
        pass
    
    @abstractmethod
    async def update(self, temporary_file: TemporaryFile) -> TemporaryFile:
        """Atualiza um arquivo temporário"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: UUID) -> bool:
        """Deleta um arquivo temporário"""
        pass
    
    @abstractmethod
    async def list_expired_files(self) -> List[TemporaryFile]:
        """Lista arquivos temporários expirados"""
        pass
    
    @abstractmethod
    async def cleanup_expired_files(self) -> int:
        """Remove arquivos temporários expirados e retorna a quantidade removida"""
        pass
    
    @abstractmethod
    async def list_by_download_id(self, download_id: UUID) -> List[TemporaryFile]:
        """Lista todos os arquivos temporários de um download"""
        pass 