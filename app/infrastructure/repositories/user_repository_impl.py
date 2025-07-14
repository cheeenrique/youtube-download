from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.domain.repositories.user_repository import UserRepository
from app.domain.entities.user import User, UserRole
from app.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """Implementação do repositório de usuários usando SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _to_entity(self, model: UserModel) -> User:
        """Converte modelo para entidade"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            salt=model.salt,
            full_name=model.full_name,
            role=UserRole(model.role),
            is_active=model.is_active,
            last_login=model.last_login,
            login_attempts=model.login_attempts,
            locked_until=model.locked_until,
            created_at=model.created_at,
            updated_at=model.updated_at,
            preferences=model.preferences or {}
        )
    
    def _to_model(self, entity: User) -> UserModel:
        """Converte entidade para modelo"""
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            hashed_password=entity.hashed_password,
            salt=entity.salt,
            full_name=entity.full_name,
            role=entity.role.value,
            is_active=entity.is_active,
            last_login=entity.last_login,
            login_count=0,  # Campo adicional no modelo
            login_attempts=entity.login_attempts,
            locked_until=entity.locked_until,
            preferences=entity.preferences,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    def create(self, user: User) -> User:
        """Cria um novo usuário"""
        model = self._to_model(user)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)
    
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Obtém um usuário pelo ID"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return None
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(model) if model else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Obtém um usuário pelo username"""
        model = self.db.query(UserModel).filter(UserModel.username == username).first()
        return self._to_entity(model) if model else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Obtém um usuário pelo email"""
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(model) if model else None
    
    def update(self, user: User) -> User:
        """Atualiza um usuário"""
        model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not model:
            raise ValueError(f"User with id {user.id} not found")
        
        # Atualiza os campos
        model.username = user.username
        model.email = user.email
        model.hashed_password = user.hashed_password
        model.salt = user.salt
        model.full_name = user.full_name
        model.role = user.role.value
        model.is_active = user.is_active
        model.last_login = user.last_login
        model.login_attempts = user.login_attempts
        model.locked_until = user.locked_until
        model.preferences = user.preferences
        model.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)
    
    def delete(self, user_id: UUID) -> bool:
        """Deleta um usuário"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        self.db.delete(model)
        self.db.commit()
        return True
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtém todos os usuários com paginação"""
        models = self.db.query(UserModel).offset(skip).limit(limit).all()
        return [self._to_entity(model) for model in models]
    
    def get_active_users(self) -> List[User]:
        """Obtém todos os usuários ativos"""
        models = self.db.query(UserModel).filter(UserModel.is_active == True).all()
        return [self._to_entity(model) for model in models]
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Obtém usuários por role"""
        models = self.db.query(UserModel).filter(UserModel.role == role.value).all()
        return [self._to_entity(model) for model in models]
    
    def search_users(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Busca usuários por nome, email ou username"""
        search_filter = or_(
            UserModel.username.ilike(f"%{query}%"),
            UserModel.email.ilike(f"%{query}%"),
            UserModel.full_name.ilike(f"%{query}%")
        )
        models = self.db.query(UserModel).filter(search_filter).offset(skip).limit(limit).all()
        return [self._to_entity(model) for model in models]
    
    def update_last_login(self, user_id: UUID) -> bool:
        """Atualiza o timestamp do último login"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        model.last_login = datetime.utcnow()
        model.login_count += 1
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def increment_login_attempts(self, user_id: UUID) -> bool:
        """Incrementa as tentativas de login"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        model.login_attempts += 1
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def reset_login_attempts(self, user_id: UUID) -> bool:
        """Reseta as tentativas de login"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        model.login_attempts = 0
        model.locked_until = None
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def lock_user(self, user_id: UUID, duration_minutes: int = 15) -> bool:
        """Bloqueia um usuário"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        model.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def unlock_user(self, user_id: UUID) -> bool:
        """Desbloqueia um usuário"""
        # Convert string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                return False
        
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        model.locked_until = None
        model.login_attempts = 0
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def change_password(self, user_id: UUID, hashed_password: str, salt: str) -> bool:
        """Altera a senha de um usuário"""
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        
        model.hashed_password = hashed_password
        model.salt = salt
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos usuários"""
        total_users = self.db.query(UserModel).count()
        active_users = self.db.query(UserModel).filter(UserModel.is_active == True).count()
        admin_users = self.db.query(UserModel).filter(UserModel.role == UserRole.ADMIN.value).count()
        
        # Registros recentes (últimos 30 dias)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = self.db.query(UserModel).filter(
            UserModel.created_at > thirty_days_ago
        ).count()
        
        # Logins recentes (últimos 7 dias)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_logins = self.db.query(UserModel).filter(
            UserModel.last_login > seven_days_ago
        ).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'recent_registrations': recent_registrations,
            'recent_logins': recent_logins,
            'registration_rate': recent_registrations / 30 if total_users > 0 else 0,
            'login_rate': recent_logins / 7 if total_users > 0 else 0
        }
    
    def get_recent_registrations(self, days: int = 30) -> List[User]:
        """Obtém registros recentes"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        models = self.db.query(UserModel).filter(
            UserModel.created_at > cutoff_date
        ).order_by(UserModel.created_at.desc()).all()
        return [self._to_entity(model) for model in models]
    
    def get_recent_logins(self, days: int = 7) -> List[User]:
        """Obtém logins recentes"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        models = self.db.query(UserModel).filter(
            UserModel.last_login > cutoff_date
        ).order_by(UserModel.last_login.desc()).all()
        return [self._to_entity(model) for model in models]
    
    def count_users(self) -> int:
        """Conta o total de usuários"""
        return self.db.query(UserModel).count()
    
    def count_active_users(self) -> int:
        """Conta usuários ativos"""
        return self.db.query(UserModel).filter(UserModel.is_active == True).count()
    
    def count_admin_users(self) -> int:
        """Conta usuários administradores"""
        return self.db.query(UserModel).filter(UserModel.role == UserRole.ADMIN.value).count() 