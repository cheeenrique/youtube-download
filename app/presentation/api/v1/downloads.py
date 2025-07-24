from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Security
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import structlog
from uuid import UUID

from app.presentation.schemas.download import (
    DownloadCreateRequest, DownloadResponse, DownloadStatusResponse,
    DownloadQueueResponse, DownloadStatsResponse, TemporaryFileResponse,
    DownloadBatchRequest, DownloadListResponse
)
from app.presentation.schemas.common import PaginationParams, PaginatedResponse
from app.infrastructure.database.connection import get_db
from app.infrastructure.repositories.download_repository_impl import SQLAlchemyDownloadRepository
from app.infrastructure.celery.tasks.download_tasks import download_video_task, process_download_queue_task
from app.infrastructure.celery.tasks.cleanup_tasks import cleanup_expired_files_task
from app.domain.entities.download import Download
from app.domain.value_objects.download_status import DownloadStatus
from app.domain.value_objects.download_quality import DownloadQuality
from app.shared.exceptions.download_exceptions import DownloadNotFoundError, InvalidURLError
from app.presentation.api.v1.auth import get_current_user

logger = structlog.get_logger()

router = APIRouter(prefix="/downloads", tags=["downloads"])


def get_download_repository(db: Session = Depends(get_db)) -> SQLAlchemyDownloadRepository:
    """Dependency para obter o repositório de downloads"""
    return SQLAlchemyDownloadRepository(db)


@router.post("/sync", response_model=DownloadResponse)
async def create_sync_download(
    download_data: DownloadCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Criar download síncrono"""
    try:
        # Verificar se já existe download para esta URL
        existing_download = await repo.get_by_url(download_data.url)
        if existing_download:
            return DownloadResponse.from_entity(existing_download)
        
        # Criar nova entidade de download
        download = Download(
            url=download_data.url,
            user_id=UUID(current_user["id"]),
            quality=DownloadQuality(download_data.quality) if download_data.quality else DownloadQuality.BEST,
            status=DownloadStatus.PENDING,
            storage_type=download_data.storage_type.value,
            uploaded_to_drive=download_data.upload_to_drive
        )
        
        # Salvar no banco
        download = await repo.create(download)
        
        # Iniciar download imediatamente
        background_tasks.add_task(
            download_video_task.delay,
            str(download.id),
            download.url,
            download.quality.value
        )
        
        logger.info("Download síncrono criado", download_id=str(download.id))
        return DownloadResponse.from_entity(download)
        
    except Exception as e:
        logger.error("Erro ao criar download síncrono", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=List[DownloadResponse])
async def create_batch_downloads(
    batch_data: DownloadBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Criar múltiplos downloads"""
    try:
        created_downloads = []
        
        for url in batch_data.urls:
            # Verificar se já existe download para esta URL
            existing_download = await repo.get_by_url(str(url))
            if existing_download:
                created_downloads.append(existing_download)
                continue
            
            # Criar nova entidade de download
            download = Download(
                url=str(url),
                user_id=UUID(current_user["id"]),
                quality=DownloadQuality(batch_data.quality) if batch_data.quality else DownloadQuality.BEST,
                status=DownloadStatus.PENDING,
                storage_type=batch_data.storage_type.value,
                uploaded_to_drive=batch_data.upload_to_drive
            )
            
            # Salvar no banco
            download = await repo.create(download)
            created_downloads.append(download)
        
        # Processar fila em background
        background_tasks.add_task(process_download_queue_task.delay)
        
        logger.info("Downloads em lote criados", count=len(created_downloads))
        return [DownloadResponse.from_entity(d) for d in created_downloads]
        
    except Exception as e:
        logger.error("Erro ao criar downloads em lote", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{download_id}", response_model=DownloadResponse)
async def get_download(
    download_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Buscar download por ID"""
    try:
        download = await repo.get_by_id(download_id)
        if not download:
            raise DownloadNotFoundError(f"Download não encontrado: {download_id}")
        
        # Verificar se o usuário tem permissão para ver este download
        if not current_user.get("is_admin") and download.user_id != UUID(current_user["id"]):
            raise HTTPException(status_code=403, detail="Acesso negado: você só pode ver seus próprios downloads")
        
        return DownloadResponse.from_entity(download)
        
    except DownloadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Erro ao buscar download", error=str(e), download_id=str(download_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DownloadListResponse)
async def list_downloads(
    status: Optional[DownloadStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(20, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Listar downloads com filtros"""
    try:
        # Se for admin, pode ver todos os downloads, senão apenas os próprios
        user_id = UUID(current_user["id"]) if not current_user.get("is_admin") else None
        
        if status:
            downloads = await repo.list_by_status(status, limit=limit, offset=offset)
            # Filtrar por usuário se não for admin
            if user_id:
                downloads = [d for d in downloads if d.user_id == user_id]
        else:
            downloads = await repo.list_all(limit=limit, offset=offset, user_id=user_id)
        
        # Aplicar paginação
        total = len(downloads)
        
        return DownloadListResponse(
            downloads=[DownloadResponse.from_entity(d) for d in downloads],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error("Erro ao listar downloads", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=DownloadStatsResponse)
async def get_download_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Obter estatísticas dos downloads"""
    try:
        # Se for admin, retorna estatísticas gerais, senão apenas do usuário
        user_id = UUID(current_user["id"]) if not current_user.get("is_admin") else None
        stats = await repo.get_download_stats(user_id=user_id)
        
        return DownloadStatsResponse(
            total_downloads=stats.get('total_downloads', 0),
            completed_downloads=stats.get('completed_downloads', 0),
            failed_downloads=stats.get('failed_downloads', 0),
            pending_downloads=stats.get('pending_downloads', 0),
            downloads_today=stats.get('downloads_today', 0),
            downloads_this_week=stats.get('downloads_this_week', 0),
            downloads_this_month=stats.get('downloads_this_month', 0),
            total_storage_used=stats.get('total_storage_used', 0),
            average_download_time=stats.get('average_download_time', 0.0)
        )
        
    except Exception as e:
        logger.error("Erro ao obter estatísticas", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{download_id}")
async def delete_download(
    download_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Deletar download"""
    try:
        # Verificar se o download existe e se o usuário tem permissão
        download = await repo.get_by_id(download_id)
        if not download:
            raise DownloadNotFoundError(f"Download não encontrado: {download_id}")
        
        # Verificar se o usuário tem permissão para deletar este download
        if not current_user.get("is_admin") and download.user_id != UUID(current_user["id"]):
            raise HTTPException(status_code=403, detail="Acesso negado: você só pode deletar seus próprios downloads")
        
        success = await repo.delete(download_id)
        if not success:
            raise DownloadNotFoundError(f"Download não encontrado: {download_id}")
        
        logger.info("Download deletado", download_id=str(download_id))
        return {"message": "Download deletado com sucesso"}
        
    except DownloadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Erro ao deletar download", error=str(e), download_id=str(download_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{download_id}/retry")
async def retry_download(
    download_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Tentar novamente um download que falhou"""
    try:
        download = await repo.get_by_id(download_id)
        if not download:
            raise DownloadNotFoundError(f"Download não encontrado: {download_id}")
        
        # Verificar se o usuário tem permissão para retry este download
        if not current_user.get("is_admin") and download.user_id != UUID(current_user["id"]):
            raise HTTPException(status_code=403, detail="Acesso negado: você só pode tentar novamente seus próprios downloads")
        
        if download.status != DownloadStatus.FAILED:
            raise HTTPException(
                status_code=400, 
                detail="Apenas downloads que falharam podem ser tentados novamente"
            )
        
        # Resetar status
        download.status = DownloadStatus.PENDING
        download.error_message = None
        download.attempts += 1
        await repo.update(download)
        
        # Adicionar à fila
        background_tasks.add_task(
            download_video_task.delay,
            str(download.id),
            download.url,
            download.quality.value
        )
        
        logger.info("Download marcado para nova tentativa", download_id=str(download.id))
        return {"message": "Download adicionado à fila para nova tentativa"}
        
    except DownloadNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Erro ao tentar novamente download", error=str(e), download_id=str(download_id))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/queue/process")
async def process_queue(
    background_tasks: BackgroundTasks
):
    """Processar fila de downloads manualmente"""
    try:
        background_tasks.add_task(process_download_queue_task.delay)
        
        logger.info("Fila de downloads processada manualmente")
        return {"message": "Fila de downloads processada"}
        
    except Exception as e:
        logger.error("Erro ao processar fila", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 


@router.post("/cleanup/temporary-files", tags=["downloads"], summary="Limpar arquivos temporários expirados", description="Dispara a limpeza de arquivos temporários expirados em background via Celery.")
async def cleanup_temporary_files(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Dispara a task Celery para limpar arquivos temporários expirados."""
    task = cleanup_expired_files_task.delay()
    return {"message": "Limpeza de arquivos temporários agendada", "task_id": task.id} 