from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.google_drive_config import GoogleDriveConfig


class GoogleDriveRepository(ABC):
    """Interface para repositório de configurações do Google Drive"""
    
    @abstractmethod
    def create(self, config: GoogleDriveConfig) -> GoogleDriveConfig:
        """Criar nova configuração"""
        pass
    
    @abstractmethod
    def get_by_id(self, config_id: UUID) -> Optional[GoogleDriveConfig]:
        """Buscar configuração por ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> Optional[GoogleDriveConfig]:
        """Buscar configuração por ID do usuário"""
        pass
    
    @abstractmethod
    def get_by_account_name(self, account_name: str) -> Optional[GoogleDriveConfig]:
        """Buscar configuração por nome da conta"""
        pass
    
    @abstractmethod
    def list_all(self, skip: int = 0, limit: int = 100) -> tuple[List[GoogleDriveConfig], int]:
        """Listar todas as configurações com paginação"""
        pass
    
    @abstractmethod
    def list_by_user_id(self, user_id: str) -> List[GoogleDriveConfig]:
        """Listar configurações por ID do usuário"""
        pass
    
    @abstractmethod
    def update(self, config: GoogleDriveConfig) -> GoogleDriveConfig:
        """Atualizar configuração"""
        pass
    
    @abstractmethod
    def delete(self, config_id: UUID) -> bool:
        """Deletar configuração"""
        pass
    
    @abstractmethod
    def get_default_config(self) -> Optional[GoogleDriveConfig]:
        """Obter configuração padrão"""
        pass
    
    @abstractmethod
    def set_default_config(self, config_id: UUID) -> bool:
        """Definir configuração como padrão"""
        pass 