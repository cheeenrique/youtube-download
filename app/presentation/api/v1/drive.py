from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog
from uuid import UUID

from app.presentation.schemas.drive import (
    DriveConfigCreateRequest, DriveConfigResponse, DriveUploadResponse,
    DriveFolderResponse, DriveQuotaResponse, DriveTestResponse,
    DriveConfigUpdateRequest, DriveUploadRequest
)
from app.presentation.schemas.common import PaginationParams, PaginatedResponse
from app.presentation.schemas.download import DownloadResponse
from app.infrastructure.database.connection import get_db
from app.infrastructure.repositories.google_drive_repository_impl import SQLAlchemyGoogleDriveRepository
from app.infrastructure.external_services.google_drive_service import GoogleDriveService
from app.infrastructure.celery.tasks.drive_tasks import (
    upload_to_drive_task,
    sync_drive_quota_task,
    test_drive_connection_task
)
from app.domain.entities.google_drive_config import GoogleDriveConfig, DriveConfigStatus
from app.shared.exceptions.drive_exceptions import (
    DriveException,
    DriveAuthenticationError,
    DriveQuotaExceededError,
    DriveFileNotFoundError,
    DriveRateLimitError
)

logger = structlog.get_logger()

router = APIRouter(prefix="/drive", tags=["drive"])


def get_drive_repository(db: Session = Depends(get_db)) -> SQLAlchemyGoogleDriveRepository:
    """Dependency para obter o repositório do Google Drive"""
    return SQLAlchemyGoogleDriveRepository(db)


@router.post("/config", response_model=DriveConfigResponse)
async def create_drive_config(
    config_data: DriveConfigCreateRequest,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Criar configuração do Google Drive"""
    try:
        # Verificar se já existe configuração para esta conta
        existing_config = repo.get_by_account_name(config_data.user_id)
        if existing_config:
            raise HTTPException(
                status_code=400,
                detail=f"Já existe configuração para a conta: {config_data.user_id}"
            )
        
        # Criar nova configuração
        config = GoogleDriveConfig(
            user_id=config_data.user_id,
            credentials=config_data.credentials,
            folder_id=config_data.folder_id,
            status=DriveConfigStatus.ACTIVE if config_data.is_default else DriveConfigStatus.INACTIVE
        )
        
        # Salvar no banco
        config = repo.create(config)
        
        logger.info("Configuração do Google Drive criada", config_id=str(config.id))
        return DriveConfigResponse.from_entity(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar configuração do Google Drive", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{config_id}", response_model=DriveConfigResponse)
async def get_drive_config(
    config_id: UUID,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Buscar configuração do Google Drive por ID"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        return DriveConfigResponse.from_entity(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao buscar configuração", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config", response_model=PaginatedResponse[DriveConfigResponse])
async def list_drive_configs(
    pagination_params: PaginationParams = Depends(),
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Listar todas as configurações do Google Drive"""
    try:
        configs, total = repo.list_all(pagination_params.skip, pagination_params.limit)
        
        return PaginatedResponse(
            items=[DriveConfigResponse.from_entity(config) for config in configs],
            total=total
        )
        
    except Exception as e:
        logger.error("Erro ao listar configurações", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/{config_id}", response_model=DriveConfigResponse)
async def update_drive_config(
    config_id: UUID,
    config_data: DriveConfigUpdateRequest,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Atualizar configuração do Google Drive"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        # Atualizar campos
        if config_data.folder_id is not None:
            config.folder_id = config_data.folder_id
        
        if config_data.is_default is not None:
            config.is_default = config_data.is_default
        
        # Salvar no banco
        config = repo.update(config)
        
        logger.info("Configuração do Google Drive atualizada", config_id=str(config_id))
        return DriveConfigResponse.from_entity(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao atualizar configuração", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/config/{config_id}")
async def delete_drive_config(
    config_id: UUID,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Deletar configuração do Google Drive"""
    try:
        success = repo.delete(config_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        logger.info("Configuração do Google Drive deletada", config_id=str(config_id))
        return {"message": "Configuração deletada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao deletar configuração", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{config_id}/folders", response_model=List[DriveFolderResponse])
async def list_drive_folders(
    config_id: UUID,
    parent_id: Optional[str] = None,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Listar pastas do Google Drive"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=config.credentials_file,
            account_name=config.user_id
        )
        
        # Listar pastas
        folders = drive_service.list_folders(parent_id=parent_id)
        
        return [DriveFolderResponse.from_drive_folder(folder) for folder in folders]
        
    except DriveAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except DriveRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao listar pastas", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{config_id}/quota", response_model=DriveQuotaResponse)
async def get_drive_quota(
    config_id: UUID,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Obter quota do Google Drive"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=config.credentials_file,
            account_name=config.user_id
        )
        
        # Obter quota
        quota_info = drive_service.get_quota_info()
        
        return DriveQuotaResponse(
            used=quota_info['used'],
            limit=quota_info['limit'],
            percentage=(quota_info['used'] / quota_info['limit'] * 100) if quota_info['limit'] > 0 else 0
        )
        
    except DriveAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter quota", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/{config_id}/test", response_model=DriveTestResponse)
async def test_drive_connection(
    config_id: UUID,
    background_tasks: BackgroundTasks,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Testar conexão com Google Drive"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        # Executar teste em background
        background_tasks.add_task(test_drive_connection_task.delay, str(config_id))
        
        logger.info("Teste de conexão com Google Drive iniciado", config_id=str(config_id))
        return {"message": "Teste de conexão iniciado. Verifique os logs para resultados."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao iniciar teste de conexão", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/{config_id}/sync-quota")
async def sync_drive_quota(
    config_id: UUID,
    background_tasks: BackgroundTasks,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Sincronizar quota do Google Drive"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        # Executar sincronização em background
        background_tasks.add_task(sync_drive_quota_task.delay, str(config_id))
        
        logger.info("Sincronização de quota iniciada", config_id=str(config_id))
        return {"message": "Sincronização de quota iniciada"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao iniciar sincronização de quota", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/downloads/{download_id}/upload")
async def upload_download_to_drive(
    download_id: UUID,
    upload_data: DriveUploadRequest,
    background_tasks: BackgroundTasks,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Fazer upload de um download para o Google Drive"""
    try:
        # Verificar se a configuração existe
        config = None
        if upload_data.config_id:
            config = repo.get_by_id(upload_data.config_id)
        else:
            config = repo.get_default_config()
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma configuração do Google Drive encontrada"
            )
        
        # Executar upload em background
        background_tasks.add_task(
            upload_to_drive_task.delay,
            str(download_id),
            str(config.id) if config else None,
            upload_data.folder_id
        )
        
        logger.info("Upload para Google Drive iniciado", 
                   download_id=str(download_id), config_id=str(config.id))
        return {"message": "Upload para Google Drive iniciado"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao iniciar upload", error=str(e), download_id=str(download_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/{config_id}/create-folder")
async def create_drive_folder(
    config_id: UUID,
    name: str,
    parent_id: Optional[str] = None,
    repo: SQLAlchemyGoogleDriveRepository = Depends(get_drive_repository)
):
    """Criar pasta no Google Drive"""
    try:
        config = repo.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuração não encontrada: {config_id}"
            )
        
        # Criar serviço do Google Drive
        drive_service = GoogleDriveService(
            credentials_file=config.credentials_file,
            account_name=config.user_id
        )
        
        # Criar pasta
        folder = drive_service.create_folder(name, parent_id)
        
        logger.info("Pasta criada no Google Drive", 
                   config_id=str(config_id), folder_name=name, folder_id=folder['id'])
        return {"folder_id": folder['id'], "name": folder['name']}
        
    except DriveAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except DriveRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar pasta", error=str(e), config_id=str(config_id))
        raise HTTPException(status_code=500, detail=str(e)) 