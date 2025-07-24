from typing import List
from celery import current_task
import structlog
from datetime import datetime, timedelta, timezone
import os
import shutil
from sqlalchemy import and_

from app.infrastructure.celery.celery_app import celery_app
from app.infrastructure.database.connection import SessionLocal
from app.infrastructure.database.models import DownloadModel, TemporaryFileModel, DownloadLog as DownloadLogModel
from app.domain.value_objects.download_status import DownloadStatus
from app.shared.config import settings
from app.infrastructure.repositories.temporary_file_repository_impl import SQLAlchemyTemporaryFileRepository
from app.infrastructure.external_services.temporary_url_service import TemporaryURLService

logger = structlog.get_logger()


@celery_app.task(name="cleanup_expired_files")
def cleanup_expired_files_task():
    """Task para limpar arquivos temporários expirados"""
    db = SessionLocal()
    try:
        # Buscar arquivos temporários expirados
        expired_files = db.query(TemporaryFileModel).filter(
            TemporaryFileModel.expiration_time < datetime.now(timezone.utc)
        ).all()
        
        deleted_count = 0
        for temp_file in expired_files:
            try:
                # Deletar arquivo físico
                if os.path.exists(temp_file.file_path):
                    os.remove(temp_file.file_path)
                    logger.info("Arquivo temporário deletado", 
                               file_path=temp_file.file_path)
                
                # Deletar registro do banco
                db.delete(temp_file)
                deleted_count += 1
                
            except Exception as e:
                logger.error("Erro ao deletar arquivo temporário", 
                           file_path=temp_file.file_path,
                           error=str(e))
        
        db.commit()
        
        logger.info("Limpeza de arquivos temporários concluída", 
                   deleted_count=deleted_count)
        
        return {
            "status": "completed",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error("Erro na limpeza de arquivos temporários", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_old_logs")
def cleanup_old_logs_task():
    """Task para limpar logs antigos"""
    db = SessionLocal()
    try:
        # Definir data limite (30 dias atrás)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Buscar logs antigos
        old_logs = db.query(DownloadLogModel).filter(
            DownloadLogModel.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for log in old_logs:
            try:
                db.delete(log)
                deleted_count += 1
            except Exception as e:
                logger.error("Erro ao deletar log", 
                           log_id=str(log.id),
                           error=str(e))
        
        db.commit()
        
        logger.info("Limpeza de logs antigos concluída", 
                   deleted_count=deleted_count)
        
        return {
            "status": "completed",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error("Erro na limpeza de logs antigos", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_failed_downloads")
def cleanup_failed_downloads_task():
    """Task para limpar downloads que falharam há muito tempo"""
    db = SessionLocal()
    try:
        # Definir data limite (7 dias atrás)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Buscar downloads que falharam há muito tempo
        old_failed_downloads = db.query(DownloadModel).filter(
            and_(
                DownloadModel.status == DownloadStatus.FAILED.value,
                DownloadModel.created_at < cutoff_date
            )
        ).all()
        
        deleted_count = 0
        for download in old_failed_downloads:
            try:
                # Deletar arquivo físico se existir
                if download.file_path and os.path.exists(download.file_path):
                    os.remove(download.file_path)
                    logger.info("Arquivo de download falhado deletado", 
                               file_path=download.file_path)
                
                # Deletar registro do banco
                db.delete(download)
                deleted_count += 1
                
            except Exception as e:
                logger.error("Erro ao deletar download falhado", 
                           download_id=str(download.id),
                           error=str(e))
        
        db.commit()
        
        logger.info("Limpeza de downloads falhados concluída", 
                   deleted_count=deleted_count)
        
        return {
            "status": "completed",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error("Erro na limpeza de downloads falhados", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_temp_directory")
def cleanup_temp_directory_task():
    """Task para limpar diretório temporário"""
    try:
        temp_dir = settings.temp_dir
        
        if not os.path.exists(temp_dir):
            logger.info("Diretório temporário não existe", temp_dir=temp_dir)
            return {"status": "no_temp_dir"}
        
        # Listar arquivos no diretório temporário
        files = os.listdir(temp_dir)
        deleted_count = 0
        
        for filename in files:
            file_path = os.path.join(temp_dir, filename)
            try:
                # Verificar se é um arquivo
                if os.path.isfile(file_path):
                    # Verificar se o arquivo é antigo (mais de 1 hora)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc)
                    if datetime.now(timezone.utc) - file_time > timedelta(hours=1):
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info("Arquivo temporário deletado", file_path=file_path)
                
                # Verificar se é um diretório
                elif os.path.isdir(file_path):
                    # Verificar se o diretório é antigo (mais de 1 hora)
                    dir_time = datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc)
                    if datetime.now(timezone.utc) - dir_time > timedelta(hours=1):
                        shutil.rmtree(file_path)
                        deleted_count += 1
                        logger.info("Diretório temporário deletado", dir_path=file_path)
                        
            except Exception as e:
                logger.error("Erro ao deletar arquivo/diretório temporário", 
                           path=file_path,
                           error=str(e))
        
        logger.info("Limpeza do diretório temporário concluída", 
                   deleted_count=deleted_count)
        
        return {
            "status": "completed",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error("Erro na limpeza do diretório temporário", error=str(e))
        raise


@celery_app.task(name="cleanup_temporary_downloads")
def cleanup_temporary_downloads_task():
    """Task para limpar downloads marcados como temporários (storage_type = 'temporary')"""
    db = SessionLocal()
    try:
        # Definir data limite (1 hora atrás)
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Buscar downloads temporários antigos
        old_temporary_downloads = db.query(DownloadModel).filter(
            and_(
                DownloadModel.storage_type == 'temporary',
                DownloadModel.created_at < cutoff_date
            )
        ).all()
        
        deleted_count = 0
        for download in old_temporary_downloads:
            try:
                # Deletar arquivo físico se existir
                if download.file_path and os.path.exists(download.file_path):
                    os.remove(download.file_path)
                    logger.info("Arquivo de download temporário deletado", 
                               file_path=download.file_path)
                
                # Deletar registro do banco
                db.delete(download)
                deleted_count += 1
                
            except Exception as e:
                logger.error("Erro ao deletar download temporário", 
                           download_id=str(download.id),
                           error=str(e))
        
        db.commit()
        
        logger.info("Limpeza de downloads temporários concluída", 
                   deleted_count=deleted_count)
        
        return {
            "status": "completed",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        db.rollback()
        logger.error("Erro na limpeza de downloads temporários", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_orphaned_files")
def cleanup_orphaned_files_task():
    """Task para limpar arquivos órfãos (sem registro no banco)"""
    db = SessionLocal()
    try:
        # Buscar todos os arquivos registrados no banco
        registered_files = db.query(DownloadModel.file_path).filter(
            DownloadModel.file_path.isnot(None)
        ).all()
        
        registered_paths = {file[0] for file in registered_files}
        
        # Verificar arquivos no diretório de vídeos
        videos_dir = settings.videos_dir
        orphaned_count = 0
        
        if os.path.exists(videos_dir):
            for root, dirs, files in os.walk(videos_dir):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    
                    # Verificar se o arquivo não está registrado no banco
                    if file_path not in registered_paths:
                        try:
                            # Verificar se o arquivo é antigo (mais de 24 horas)
                            file_time = datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc)
                            if datetime.now(timezone.utc) - file_time > timedelta(hours=24):
                                os.remove(file_path)
                                orphaned_count += 1
                                logger.info("Arquivo órfão deletado", file_path=file_path)
                                
                        except Exception as e:
                            logger.error("Erro ao deletar arquivo órfão", 
                                       file_path=file_path,
                                       error=str(e))
        
        logger.info("Limpeza de arquivos órfãos concluída", 
                   deleted_count=orphaned_count)
        
        return {
            "status": "completed",
            "deleted_count": orphaned_count
        }
        
    except Exception as e:
        logger.error("Erro na limpeza de arquivos órfãos", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_temp_urls")
def cleanup_temp_urls_task():
    """Task para limpar links temporários expirados"""
    db = SessionLocal()
    try:
        # Criar repositório e serviço
        temp_file_repo = SQLAlchemyTemporaryFileRepository(db)
        temp_url_service = TemporaryURLService(temp_file_repo)
        
        # Executar limpeza
        cleaned_count = temp_url_service.cleanup_expired_urls()
        
        logger.info("Limpeza de links temporários concluída", cleaned_count=cleaned_count)
        
        return {
            'status': 'completed',
            'cleaned_count': cleaned_count,
            'message': f'Limpeza concluída: {cleaned_count} links removidos'
        }
        
    except Exception as e:
        logger.error("Erro na limpeza de links temporários", error=str(e))
        raise
    
    finally:
        db.close()


@celery_app.task(name="cleanup_temp_urls_db_only")
def cleanup_temp_urls_db_only_task():
    """Task para limpar links temporários expirados (apenas do banco)"""
    db = SessionLocal()
    try:
        # Criar repositório
        temp_file_repo = SQLAlchemyTemporaryFileRepository(db)
        
        # Deletar registros expirados do banco
        deleted_count = temp_file_repo.delete_expired_files()
        
        logger.info("Limpeza de links temporários (apenas DB) concluída", deleted_count=deleted_count)
        
        return {
            'status': 'completed',
            'deleted_count': deleted_count,
            'message': f'Limpeza concluída: {deleted_count} links removidos do banco'
        }
        
    except Exception as e:
        logger.error("Erro na limpeza de links temporários (apenas DB)", error=str(e))
        raise
    
    finally:
        db.close() 