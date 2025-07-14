from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum


class UserRole(str, Enum):
    """Roles de usuário"""
    USER = "user"
    ADMIN = "admin"


class User:
    """Entidade para representar um usuário do sistema"""
    
    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        salt: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
        id: Optional[UUID] = None,
        last_login: Optional[datetime] = None,
        login_attempts: int = 0,
        locked_until: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        preferences: Optional[Dict[str, Any]] = None
    ):
        self.id = id or uuid4()
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.salt = salt
        self.full_name = full_name
        self.role = role
        self.is_active = is_active
        self.last_login = last_login
        self.login_attempts = login_attempts
        self.locked_until = locked_until
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.preferences = preferences or {}

    @property
    def is_admin(self) -> bool:
        """Verifica se o usuário é administrador"""
        return self.role == UserRole.ADMIN

    @property
    def is_locked(self) -> bool:
        """Verifica se a conta está bloqueada"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until

    def can_login(self) -> bool:
        """Verifica se o usuário pode fazer login"""
        return self.is_active and not self.is_locked

    def increment_login_attempts(self) -> None:
        """Incrementa as tentativas de login"""
        self.login_attempts += 1
        self.updated_at = datetime.utcnow()

    def reset_login_attempts(self) -> None:
        """Reseta as tentativas de login"""
        self.login_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.utcnow()

    def lock_account(self, duration_minutes: int = 15) -> None:
        """Bloqueia a conta por um período"""
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.updated_at = datetime.utcnow()

    def unlock_account(self) -> None:
        """Desbloqueia a conta"""
        self.locked_until = None
        self.login_attempts = 0
        self.updated_at = datetime.utcnow()

    def update_last_login(self) -> None:
        """Atualiza o timestamp do último login"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def change_password(self, new_hashed_password: str, new_salt: str) -> None:
        """Altera a senha do usuário"""
        self.hashed_password = new_hashed_password
        self.salt = new_salt
        self.updated_at = datetime.utcnow()

    def update_profile(self, full_name: Optional[str] = None, email: Optional[str] = None) -> None:
        """Atualiza o perfil do usuário"""
        if full_name is not None:
            self.full_name = full_name
        if email is not None:
            self.email = email
        self.updated_at = datetime.utcnow()

    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Atualiza as preferências do usuário"""
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Ativa a conta do usuário"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Desativa a conta do usuário"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def promote_to_admin(self) -> None:
        """Promove o usuário para administrador"""
        self.role = UserRole.ADMIN
        self.updated_at = datetime.utcnow()

    def demote_from_admin(self) -> None:
        """Remove privilégios de administrador"""
        self.role = UserRole.USER
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Converte a entidade para dicionário"""
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_attempts': self.login_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'is_locked': self.is_locked,
            'can_login': self.can_login(),
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>" 