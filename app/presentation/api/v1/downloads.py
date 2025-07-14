from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
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
from app.domain.entities.download import Download
from app.domain.value_objects.download_status import DownloadStatus
from app.domain.value_objects.download_quality import DownloadQuality
from app.shared.exceptions.download_exceptions import DownloadNotFoundError, InvalidURLError

logger = structlog.get_logger()

router = APIRouter(prefix="/downloads", tags=["downloads"])


def get_download_repository(db: Session = Depends(get_db)) -> SQLAlchemyDownloadRepository:
    """Dependency para obter o repositório de downloads"""
    return SQLAlchemyDownloadRepository(db)


@router.post("/sync", response_model=DownloadResponse)
async def create_sync_download(
    download_data: DownloadCreateRequest,
    background_tasks: BackgroundTasks,
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Criar download síncrono"""
    try:
        # Verificar se já existe download para esta URL
        existing_download = repo.get_by_url(download_data.url)
        if existing_download:
            return DownloadResponse.from_entity(existing_download)
        
        # Criar nova entidade de download
        download = Download(
            url=download_data.url,
            quality=DownloadQuality(download_data.quality) if download_data.quality else DownloadQuality.BEST,
            status=DownloadStatus.PENDING
        )
        
        # Salvar no banco
        download = repo.create(download)
        
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
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Criar múltiplos downloads"""
    try:
        created_downloads = []
        
        for url in batch_data.urls:
            # Verificar se já existe download para esta URL
            existing_download = repo.get_by_url(str(url))
            if existing_download:
                created_downloads.append(existing_download)
                continue
            
            # Criar nova entidade de download
            download = Download(
                url=str(url),
                quality=DownloadQuality(batch_data.quality) if batch_data.quality else DownloadQuality.BEST,
                status=DownloadStatus.PENDING
            )
            
            # Salvar no banco
            download = repo.create(download)
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
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Buscar download por ID"""
    try:
        download = repo.get_by_id(download_id)
        if not download:
            raise DownloadNotFoundError(f"Download não encontrado: {download_id}")
        
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
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Listar downloads com filtros"""
    try:
        if status:
            downloads = repo.get_downloads_by_status(status)
        else:
            downloads = repo.get_recent_downloads(limit=limit)
        
        # Aplicar paginação
        total = len(downloads)
        downloads = downloads[offset:offset + limit]
        
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
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Obter estatísticas dos downloads"""
    try:
        stats = repo.get_download_stats()
        
        return DownloadStatsResponse(
            total=stats.get('total', 0),
            pending=stats.get('pending', 0),
            downloading=stats.get('downloading', 0),
            completed=stats.get('completed', 0),
            failed=stats.get('failed', 0)
        )
        
    except Exception as e:
        logger.error("Erro ao obter estatísticas", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{download_id}")
async def delete_download(
    download_id: UUID,
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Deletar download"""
    try:
        success = repo.delete(download_id)
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
    repo: SQLAlchemyDownloadRepository = Depends(get_download_repository)
):
    """Tentar novamente um download que falhou"""
    try:
        download = repo.get_by_id(download_id)
        if not download:
            raise DownloadNotFoundError(f"Download não encontrado: {download_id}")
        
        if download.status != DownloadStatus.FAILED:
            raise HTTPException(
                status_code=400, 
                detail="Apenas downloads que falharam podem ser tentados novamente"
            )
        
        # Resetar status
        download.status = DownloadStatus.PENDING
        download.error_message = None
        download.attempts += 1
        repo.update(download)
        
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