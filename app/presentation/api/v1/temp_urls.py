from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import structlog
from uuid import UUID
import os

from app.presentation.schemas.temp_urls import (
    TemporaryURLCreateRequest,
    TemporaryURLResponse,
    TemporaryURLInfoResponse,
    TemporaryURLExtendRequest,
    TemporaryURLAccessLogResponse
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.repositories.download_repository_impl import SQLAlchemyDownloadRepository
from app.infrastructure.repositories.temporary_file_repository_impl import SQLAlchemyTemporaryFileRepository
from app.infrastructure.external_services.temporary_url_service import TemporaryURLService
from app.shared.exceptions.download_exceptions import (
    TemporaryFileExpiredError,
    TemporaryFileNotFoundError,
    TemporaryFileAccessDeniedError
)

logger = structlog.get_logger()

router = APIRouter(tags=["temp_urls"])


def get_temp_url_service(db: Session = Depends(get_db)) -> TemporaryURLService:
    """Dependency para obter o serviço de links temporários"""
    temp_file_repo = SQLAlchemyTemporaryFileRepository(db)
    return TemporaryURLService(temp_file_repo)


@router.post("/{download_id}/temp", response_model=TemporaryURLResponse)
async def create_temporary_url(
    download_id: UUID,
    request: TemporaryURLCreateRequest,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service),
    db: Session = Depends(get_db)
):
    """Criar link temporário para um download"""
    try:
        # Verificar se o download existe e está concluído
        download_repo = SQLAlchemyDownloadRepository(db)
        download = download_repo.get_by_id(download_id)
        
        if not download:
            raise HTTPException(
                status_code=404,
                detail=f"Download não encontrado: {download_id}"
            )
        
        if not download.file_path or not os.path.exists(download.file_path):
            raise HTTPException(
                status_code=404,
                detail="Arquivo do download não encontrado"
            )
        
        # Gerar link temporário
        temp_file = temp_url_service.generate_temporary_url(
            download_id=download_id,
            file_path=download.file_path,
            expiration_hours=request.expiration_hours,
            max_accesses=request.max_accesses,
            custom_filename=request.custom_filename
        )
        
        logger.info("Link temporário criado", 
                   download_id=str(download_id),
                   temp_url_id=str(temp_file.id))
        
        return TemporaryURLResponse.from_entity(temp_file)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao criar link temporário", 
                    error=str(e), download_id=str(download_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{download_id}/temp/{token}")
async def access_temporary_url(
    download_id: UUID,
    token: str,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service)
):
    """Acessar arquivo via link temporário"""
    try:
        # Validar link temporário
        temp_file = temp_url_service.validate_temporary_url(download_id, token)
        
        # Verificar se o arquivo existe
        if not os.path.exists(temp_file.file_path):
            raise HTTPException(
                status_code=404,
                detail="Arquivo não encontrado no servidor"
            )
        
        # Determinar nome do arquivo para download
        filename = temp_file.custom_filename or os.path.basename(temp_file.file_path)
        
        # Retornar arquivo
        return FileResponse(
            path=temp_file.file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except TemporaryFileExpiredError:
        raise HTTPException(
            status_code=410,
            detail="Link temporário expirado"
        )
    except TemporaryFileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Link temporário não encontrado"
        )
    except TemporaryFileAccessDeniedError:
        raise HTTPException(
            status_code=403,
            detail="Limite de acessos excedido"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao acessar link temporário", 
                    error=str(e), download_id=str(download_id), token=token)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{download_id}/temp/{token}/info", response_model=TemporaryURLInfoResponse)
async def get_temporary_url_info(
    download_id: UUID,
    token: str,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service)
):
    """Obter informações de um link temporário"""
    try:
        info = temp_url_service.get_temporary_url_info(download_id, token)
        
        if not info:
            raise HTTPException(
                status_code=404,
                detail="Link temporário não encontrado"
            )
        
        return TemporaryURLInfoResponse(**info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao obter informações do link temporário", 
                    error=str(e), download_id=str(download_id), token=token)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{download_id}/temp/{token}/extend", response_model=TemporaryURLResponse)
async def extend_temporary_url(
    download_id: UUID,
    token: str,
    request: TemporaryURLExtendRequest,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service)
):
    """Estender validade de um link temporário"""
    try:
        temp_file = temp_url_service.extend_temporary_url(
            download_id, token, request.additional_hours
        )
        
        if not temp_file:
            raise HTTPException(
                status_code=404,
                detail="Link temporário não encontrado ou já expirado"
            )
        
        logger.info("Link temporário estendido", 
                   download_id=str(download_id), token=token)
        
        return TemporaryURLResponse.from_entity(temp_file)
        
    except TemporaryFileExpiredError:
        raise HTTPException(
            status_code=410,
            detail="Link temporário já expirado"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao estender link temporário", 
                    error=str(e), download_id=str(download_id), token=token)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{download_id}/temp/{token}")
async def revoke_temporary_url(
    download_id: UUID,
    token: str,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service)
):
    """Revogar um link temporário"""
    try:
        success = temp_url_service.revoke_temporary_url(download_id, token)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Link temporário não encontrado"
            )
        
        logger.info("Link temporário revogado", 
                   download_id=str(download_id), token=token)
        
        return {"message": "Link temporário revogado com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro ao revogar link temporário", 
                    error=str(e), download_id=str(download_id), token=token)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{download_id}/temp/logs", response_model=list[TemporaryURLAccessLogResponse])
async def get_temporary_url_logs(
    download_id: UUID,
    limit: int = 100,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service)
):
    """Obter logs de acesso de links temporários para um download"""
    try:
        logs = temp_url_service.get_access_logs(download_id, limit)
        
        return [TemporaryURLAccessLogResponse(**log) for log in logs]
        
    except Exception as e:
        logger.error("Erro ao obter logs de acesso", 
                    error=str(e), download_id=str(download_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/temp/cleanup")
async def cleanup_expired_temp_urls(
    background_tasks: BackgroundTasks,
    temp_url_service: TemporaryURLService = Depends(get_temp_url_service)
):
    """Limpar links temporários expirados"""
    try:
        # Executar limpeza em background
        from app.infrastructure.celery.tasks.cleanup_tasks import cleanup_temp_urls_task
        background_tasks.add_task(cleanup_temp_urls_task.delay)
        
        logger.info("Limpeza de links temporários iniciada")
        return {"message": "Limpeza de links temporários iniciada"}
        
    except Exception as e:
        logger.error("Erro ao iniciar limpeza de links temporários", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 