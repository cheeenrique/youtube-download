from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.entities.user import User, UserRole


class UserRepository(ABC):
    """Interface para o repositório de usuários"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Cria um novo usuário"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtém um usuário pelo ID"""
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Obtém um usuário pelo username"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtém um usuário pelo email"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Atualiza um usuário"""
        pass
    
    @abstractmethod
    def delete(self, user_id: UUID) -> bool:
        """Deleta um usuário"""
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtém todos os usuários com paginação"""
        pass
    
    @abstractmethod
    def get_active_users(self) -> List[User]:
        """Obtém todos os usuários ativos"""
        pass
    
    @abstractmethod
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Obtém usuários por role"""
        pass
    
    @abstractmethod
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Busca usuários por nome, email ou username"""
        pass
    
    @abstractmethod
    def update_last_login(self, user_id: UUID) -> bool:
        """Atualiza o timestamp do último login"""
        pass
    
    @abstractmethod
    def increment_login_attempts(self, user_id: UUID) -> bool:
        """Incrementa as tentativas de login"""
        pass
    
    @abstractmethod
    def reset_login_attempts(self, user_id: UUID) -> bool:
        """Reseta as tentativas de login"""
        pass
    
    @abstractmethod
    def lock_user(self, user_id: UUID, duration_minutes: int = 15) -> bool:
        """Bloqueia um usuário"""
        pass
    
    @abstractmethod
    def unlock_user(self, user_id: UUID) -> bool:
        """Desbloqueia um usuário"""
        pass
    
    @abstractmethod
    def change_password(self, user_id: UUID, hashed_password: str, salt: str) -> bool:
        """Altera a senha de um usuário"""
        pass
    
    @abstractmethod
    def get_user_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos usuários"""
        pass
    
    @abstractmethod
    def get_recent_registrations(self, days: int = 30) -> List[User]:
        """Obtém registros recentes"""
        pass
    
    @abstractmethod
    def get_recent_logins(self, days: int = 7) -> List[User]:
        """Obtém logins recentes"""
        pass
    
    @abstractmethod
    def count_users(self) -> int:
        """Conta o total de usuários"""
        pass
    
    @abstractmethod
    def count_active_users(self) -> int:
        """Conta usuários ativos"""
        pass
    
    @abstractmethod
    def count_admin_users(self) -> int:
        """Conta usuários administradores"""
        pass 