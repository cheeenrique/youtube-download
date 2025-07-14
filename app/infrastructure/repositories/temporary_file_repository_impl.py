from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta, timezone
import structlog
from uuid import UUID

from app.domain.entities.temporary_file import TemporaryFile
from app.domain.repositories.temporary_file_repository import TemporaryFileRepository
from app.infrastructure.database.models import TemporaryFileModel

logger = structlog.get_logger()


class SQLAlchemyTemporaryFileRepository(TemporaryFileRepository):
    """Implementação do TemporaryFileRepository usando SQLAlchemy"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, temp_file: TemporaryFile) -> TemporaryFile:
        """Cria um novo arquivo temporário"""
        try:
            temp_file_model = TemporaryFileModel(
                id=temp_file.id,
                download_id=temp_file.download_id,
                file_path=temp_file.file_path,
                expiration_time=temp_file.expiration_time,
                access_count=temp_file.access_count,
                temporary_url=temp_file.temporary_url,
                file_hash=temp_file.file_hash,
                max_accesses=temp_file.max_accesses,
                custom_filename=temp_file.custom_filename,
                created_at=temp_file.created_at
            )
            
            self.db.add(temp_file_model)
            self.db.commit()
            self.db.refresh(temp_file_model)
            
            logger.info("Arquivo temporário criado", temp_file_id=str(temp_file.id))
            return self._to_entity(temp_file_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao criar arquivo temporário", error=str(e), temp_file_id=str(temp_file.id))
            raise
    
    def get_by_id(self, temp_file_id: UUID) -> Optional[TemporaryFile]:
        """Busca um arquivo temporário por ID"""
        try:
            temp_file_model = self.db.query(TemporaryFileModel).filter(
                TemporaryFileModel.id == temp_file_id
            ).first()
            
            if temp_file_model:
                return self._to_entity(temp_file_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar arquivo temporário por ID", error=str(e), temp_file_id=str(temp_file_id))
            raise
    
    def get_by_download_id(self, download_id: UUID) -> List[TemporaryFile]:
        """Busca arquivos temporários por download ID"""
        try:
            temp_file_models = self.db.query(TemporaryFileModel).filter(
                TemporaryFileModel.download_id == download_id
            ).order_by(desc(TemporaryFileModel.created_at)).all()
            
            return [self._to_entity(model) for model in temp_file_models]
            
        except Exception as e:
            logger.error("Erro ao buscar arquivos temporários por download", error=str(e), download_id=str(download_id))
            raise
    
    def get_by_download_and_token(self, download_id: UUID, token: str) -> Optional[TemporaryFile]:
        """Busca arquivo temporário por download ID e token"""
        try:
            temp_file_model = self.db.query(TemporaryFileModel).filter(
                and_(
                    TemporaryFileModel.download_id == download_id,
                    TemporaryFileModel.temporary_url.like(f"%{token}")
                )
            ).first()
            
            if temp_file_model:
                return self._to_entity(temp_file_model)
            return None
            
        except Exception as e:
            logger.error("Erro ao buscar arquivo temporário por token", error=str(e), download_id=str(download_id), token=token)
            raise
    
    def get_expired_files(self) -> List[TemporaryFile]:
        """Busca arquivos temporários expirados"""
        try:
            temp_file_models = self.db.query(TemporaryFileModel).filter(
                TemporaryFileModel.expiration_time < datetime.now(timezone.utc)
            ).all()
            
            return [self._to_entity(model) for model in temp_file_models]
            
        except Exception as e:
            logger.error("Erro ao buscar arquivos temporários expirados", error=str(e))
            raise
    
    def update(self, temp_file: TemporaryFile) -> TemporaryFile:
        """Atualiza um arquivo temporário"""
        try:
            temp_file_model = self.db.query(TemporaryFileModel).filter(
                TemporaryFileModel.id == temp_file.id
            ).first()
            
            if not temp_file_model:
                raise ValueError(f"Arquivo temporário não encontrado: {temp_file.id}")
            
            # Atualizar campos
            temp_file_model.access_count = temp_file.access_count
            temp_file_model.expiration_time = temp_file.expiration_time
            temp_file_model.last_accessed = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(temp_file_model)
            
            logger.info("Arquivo temporário atualizado", temp_file_id=str(temp_file.id))
            return self._to_entity(temp_file_model)
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao atualizar arquivo temporário", error=str(e), temp_file_id=str(temp_file.id))
            raise
    
    def delete(self, temp_file_id: UUID) -> bool:
        """Deleta um arquivo temporário"""
        try:
            temp_file_model = self.db.query(TemporaryFileModel).filter(
                TemporaryFileModel.id == temp_file_id
            ).first()
            
            if not temp_file_model:
                return False
            
            self.db.delete(temp_file_model)
            self.db.commit()
            
            logger.info("Arquivo temporário deletado", temp_file_id=str(temp_file_id))
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao deletar arquivo temporário", error=str(e), temp_file_id=str(temp_file_id))
            raise
    
    def delete_expired_files(self) -> int:
        """Deleta arquivos temporários expirados"""
        try:
            expired_count = self.db.query(TemporaryFileModel).filter(
                TemporaryFileModel.expiration_time < datetime.now(timezone.utc)
            ).delete()
            
            self.db.commit()
            
            logger.info("Arquivos temporários expirados deletados", count=expired_count)
            return expired_count
            
        except Exception as e:
            self.db.rollback()
            logger.error("Erro ao deletar arquivos temporários expirados", error=str(e))
            raise
    
    def get_stats(self) -> dict:
        """Obtém estatísticas dos arquivos temporários"""
        try:
            total_files = self.db.query(func.count(TemporaryFileModel.id)).scalar()
            expired_files = self.db.query(func.count(TemporaryFileModel.id)).filter(
                TemporaryFileModel.expiration_time < datetime.now(timezone.utc)
            ).scalar()
            active_files = total_files - expired_files
            
            total_accesses = self.db.query(func.sum(TemporaryFileModel.access_count)).scalar() or 0
            
            return {
                'total_files': total_files,
                'active_files': active_files,
                'expired_files': expired_files,
                'total_accesses': total_accesses
            }
            
        except Exception as e:
            logger.error("Erro ao obter estatísticas dos arquivos temporários", error=str(e))
            raise
    
    def _to_entity(self, model: TemporaryFileModel) -> TemporaryFile:
        """Converte modelo SQLAlchemy para entidade do domínio"""
        return TemporaryFile(
            id=model.id,
            download_id=model.download_id,
            file_path=model.file_path,
            expiration_time=model.expiration_time,
            access_count=model.access_count,
            temporary_url=model.temporary_url,
            file_hash=model.file_hash,
            max_accesses=model.max_accesses,
            custom_filename=model.custom_filename,
            created_at=model.created_at
        ) 