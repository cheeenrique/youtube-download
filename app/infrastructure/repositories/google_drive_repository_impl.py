from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timezone
import structlog
from uuid import UUID
import json
import os

from app.domain.entities.google_drive_config import GoogleDriveConfig, DriveConfigStatus
from app.domain.repositories.google_drive_repository import GoogleDriveRepository
from app.infrastructure.database.models import GoogleDriveConfigModel
from app.infrastructure.database.connection import get_db

logger = structlog.get_logger()


class SQLAlchemyGoogleDriveRepository(GoogleDriveRepository):
    """Implementação do GoogleDriveRepository usando SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, config: GoogleDriveConfig) -> GoogleDriveConfig:
        """Cria uma nova configuração do Google Drive"""
        try:
            # Salvar credenciais em arquivo
            credentials_file = self._save_credentials(config)
            
            config_model = GoogleDriveConfigModel(
                id=config.id,
                account_name=config.user_id,
                credentials_file=credentials_file,
                folder_id=config.folder_id,
                is_active=config.status == DriveConfigStatus.ACTIVE,
                quota_used=config.quota_used,
                quota_limit=config.quota_limit,
                last_used=config.last_sync,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            
            self.db.add(config_model)
            self.db.commit()
            self.db.refresh(config_model)
            
            logger.info("Configuração do Google Drive criada", config_id=str(config.id))
            return self._to_entity(config_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao criar configuração do Google Drive", error=str(e), config_id=str(config.id))
            raise
    
    def get_by_id(self, config_id: UUID) -> Optional[GoogleDriveConfig]:
        """Busca uma configuração por ID"""
        try:
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.id == config_id
            ).first()
            
            if config_model:
                return self._to_entity(config_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar configuração por ID", error=str(e), config_id=str(config_id))
            raise
    
    def get_by_account_name(self, account_name: str) -> Optional[GoogleDriveConfig]:
        """Busca uma configuração por nome da conta"""
        try:
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.account_name == account_name
            ).first()
            
            if config_model:
                return self._to_entity(config_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar configuração por conta", error=str(e), account_name=account_name)
            raise
    
    def get_active_configs(self) -> List[GoogleDriveConfig]:
        """Busca configurações ativas"""
        try:
            config_models = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.is_active == True
            ).all()
            
            return [self._to_entity(model) for model in config_models]
            
        except Exception as e:
            logger.error("Erro ao buscar configurações ativas", error=str(e))
            raise
    
    def get_default_config(self) -> Optional[GoogleDriveConfig]:
        """Busca a configuração padrão"""
        try:
            # Por enquanto, retorna a primeira configuração ativa
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.is_active == True
            ).first()
            
            if config_model:
                return self._to_entity(config_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar configuração padrão", error=str(e))
            raise
    
    def update(self, config: GoogleDriveConfig) -> GoogleDriveConfig:
        """Atualiza uma configuração"""
        try:
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.id == config.id
            ).first()
            
            if not config_model:
                raise ValueError(f"Configuração não encontrada: {config.id}")
            
            # Atualizar campos
            config_model.account_name = config.user_id
            config_model.folder_id = config.folder_id
            config_model.is_active = config.status == DriveConfigStatus.ACTIVE
            config_model.quota_used = config.quota_used
            config_model.quota_limit = config.quota_limit
            config_model.last_used = config.last_sync
            config_model.updated_at = datetime.now(timezone.utc)
            
            # Atualizar credenciais se necessário
            if config.credentials:
                credentials_file = self._save_credentials(config)
                config_model.credentials_file = credentials_file
            
            self.db.commit()
            self.db.refresh(config_model)
            
            logger.info("Configuração do Google Drive atualizada", config_id=str(config.id))
            return self._to_entity(config_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao atualizar configuração", error=str(e), config_id=str(config.id))
            raise
    
    def delete(self, config_id: UUID) -> bool:
        """Deleta uma configuração"""
        try:
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.id == config_id
            ).first()
            
            if not config_model:
                return False
            
            # Deletar arquivo de credenciais
            if os.path.exists(config_model.credentials_file):
                os.remove(config_model.credentials_file)
            
            self.db.delete(config_model)
            self.db.commit()
            
            logger.info("Configuração do Google Drive deletada", config_id=str(config_id))
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao deletar configuração", error=str(e), config_id=str(config_id))
            raise
    
    def list_all(self) -> List[GoogleDriveConfig]:
        """Lista todas as configurações"""
        try:
            config_models = self.db.query(GoogleDriveConfigModel).order_by(
                desc(GoogleDriveConfigModel.created_at)
            ).all()
            
            return [self._to_entity(model) for model in config_models]
            
        except Exception as e:
            logger.error("Erro ao listar configurações", error=str(e))
            raise
    
    def get_configs_by_status(self, status: DriveConfigStatus) -> List[GoogleDriveConfig]:
        """Busca configurações por status"""
        try:
            is_active = status == DriveConfigStatus.ACTIVE
            config_models = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.is_active == is_active
            ).all()
            
            return [self._to_entity(model) for model in config_models]
            
        except Exception as e:
            logger.error("Erro ao buscar configurações por status", error=str(e), status=status.value)
            raise
    
    def update_quota(self, config_id: UUID, used: int, limit: Optional[int] = None) -> bool:
        """Atualiza quota de uma configuração"""
        try:
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.id == config_id
            ).first()
            
            if not config_model:
                return False
            
            config_model.quota_used = used
            if limit:
                config_model.quota_limit = limit
            config_model.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info("Quota atualizada", config_id=str(config_id), used=used, limit=limit)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao atualizar quota", error=str(e), config_id=str(config_id))
            raise
    
    def update_last_used(self, config_id: UUID) -> bool:
        """Atualiza último uso de uma configuração"""
        try:
            config_model = self.db.query(GoogleDriveConfigModel).filter(
                GoogleDriveConfigModel.id == config_id
            ).first()
            
            if not config_model:
                return False
            
            config_model.last_used = datetime.now(timezone.utc)
            config_model.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info("Último uso atualizado", config_id=str(config_id))
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao atualizar último uso", error=str(e), config_id=str(config_id))
            raise
    
    def _save_credentials(self, config: GoogleDriveConfig) -> str:
        """Salva credenciais em arquivo"""
        try:
            # Criar diretório para credenciais se não existir
            credentials_dir = "credentials"
            os.makedirs(credentials_dir, exist_ok=True)
            
            # Nome do arquivo baseado no ID da configuração
            filename = f"{config.id}.json"
            file_path = os.path.join(credentials_dir, filename)
            
            # Salvar credenciais
            with open(file_path, 'w') as f:
                json.dump(config.credentials, f, indent=2)
            
            return file_path
            
        except Exception as e:
            logger.error("Erro ao salvar credenciais", error=str(e))
            raise
    
    def _load_credentials(self, file_path: str) -> Dict[str, Any]:
        """Carrega credenciais de arquivo"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Erro ao carregar credenciais", error=str(e), file_path=file_path)
            return {}
    
    def _to_entity(self, model: GoogleDriveConfigModel) -> GoogleDriveConfig:
        """Converte modelo SQLAlchemy para entidade do domínio"""
        # Carregar credenciais
        credentials = self._load_credentials(model.credentials_file)
        
        # Determinar status
        status = DriveConfigStatus.ACTIVE if model.is_active else DriveConfigStatus.INACTIVE
        
        return GoogleDriveConfig(
            id=model.id,
            user_id=model.account_name,
            credentials=credentials,
            folder_id=model.folder_id,
            status=status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_sync=model.last_used,
            quota_used=model.quota_used,
            quota_limit=model.quota_limit,
            is_default=False  # Por enquanto, sempre False
        ) 