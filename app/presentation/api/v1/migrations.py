from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import subprocess
import sys
import os
from typing import Dict, Any
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/migrate", tags=["Migrations"])
async def run_migrations() -> Dict[str, Any]:
    """
    Endpoint temporário para executar migrações Alembic.
    ATENÇÃO: Este endpoint deve ser removido em produção!
    """
    try:
        logger.info("Iniciando execução de migrações Alembic...")
        
        # Comando para executar as migrações
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            logger.info("Migrações executadas com sucesso")
            return {
                "success": True,
                "message": "Migrações executadas com sucesso",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            logger.error(f"Erro ao executar migrações: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao executar migrações: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"Exceção ao executar migrações: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.post("/migrate/stamp", tags=["Migrations"])
async def stamp_migrations() -> Dict[str, Any]:
    """
    Marca as migrações como aplicadas sem executá-las.
    Útil quando o banco já tem a estrutura mas o Alembic não sabe.
    """
    try:
        logger.info("Marcando migrações como aplicadas...")
        
        # Comando para marcar como aplicada
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "stamp", "head"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            logger.info("Migrações marcadas como aplicadas com sucesso")
            return {
                "success": True,
                "message": "Migrações marcadas como aplicadas com sucesso",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            logger.error(f"Erro ao marcar migrações: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao marcar migrações: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"Exceção ao marcar migrações: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/migrate/status", tags=["Migrations"])
async def get_migration_status() -> Dict[str, Any]:
    """
    Verifica o status atual das migrações Alembic.
    """
    try:
        logger.info("Verificando status das migrações...")
        
        # Comando para verificar o status
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "current_revision": result.stdout.strip(),
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            logger.error(f"Erro ao verificar status: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao verificar status: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"Exceção ao verificar status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@router.get("/migrate/history", tags=["Migrations"])
async def get_migration_history() -> Dict[str, Any]:
    """
    Obtém o histórico de migrações Alembic.
    """
    try:
        logger.info("Obtendo histórico de migrações...")
        
        # Comando para obter o histórico
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "history"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "history": result.stdout,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            logger.error(f"Erro ao obter histórico: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao obter histórico: {result.stderr}"
            )
            
    except Exception as e:
        logger.error(f"Exceção ao obter histórico: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        ) 