from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging

from app.presentation.schemas.optimization import (
    CacheStatsResponse,
    PerformanceReportResponse,
    OptimizationStatusResponse,
    CompressionRequest,
    CompressionResponse,
    CacheCleanupRequest,
    CacheCleanupResponse,
    OptimizationTaskResponse,
    DatabaseOptimizationResponse,
    MemoryUsageResponse
)
from app.infrastructure.cache.mock_cache import mock_cache as redis_cache
from app.infrastructure.cache.analytics_cache import analytics_cache
from app.infrastructure.optimization.performance_optimizer import performance_optimizer
from app.infrastructure.optimization.compression_service import compression_service
from app.infrastructure.celery.tasks.optimization_tasks import (
    cleanup_cache_task,
    analyze_performance_task,
    optimize_database_task,
    compress_old_data_task,
    cleanup_compressed_files_task,
    monitor_cache_health_task,
    optimize_analytics_cache_task,
    generate_optimization_report_task,
    daily_maintenance_task,
    weekly_maintenance_task
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/optimization", tags=["Otimização"])


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Obtém estatísticas do cache Redis"""
    try:
        # Estatísticas do Redis
        redis_stats = redis_cache.get_stats()
        memory_usage = redis_cache.get_memory_usage()
        
        # Estatísticas do cache de analytics
        analytics_stats = analytics_cache.get_cache_stats()
        
        return CacheStatsResponse(
            success=True,
            redis_stats=redis_stats,
            memory_usage=memory_usage,
            analytics_stats=analytics_stats,
            cache_healthy=redis_cache.ping()
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.post("/cache/cleanup", response_model=CacheCleanupResponse)
async def cleanup_cache(request: CacheCleanupRequest, background_tasks: BackgroundTasks):
    """Limpa cache baseado nos parâmetros especificados"""
    try:
        # Executa limpeza em background
        task = cleanup_cache_task.delay(
            cache_type=request.cache_type,
            older_than_hours=request.older_than_hours
        )
        
        return CacheCleanupResponse(
            success=True,
            task_id=task.id,
            message=f"Limpeza de cache agendada para {request.cache_type}",
            cache_type=request.cache_type,
            older_than_hours=request.older_than_hours
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar limpeza de cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar limpeza: {str(e)}")


@router.delete("/cache/clear/{cache_type}")
async def clear_cache(cache_type: str):
    """Remove todas as chaves de um tipo específico de cache"""
    try:
        if cache_type == "all":
            cache_types = ['analytics', 'download', 'user', 'stats', 'reports', 'temp_url', 'drive', 'system']
        else:
            cache_types = [cache_type]
        
        total_cleared = 0
        for ct in cache_types:
            if redis_cache.clear_prefix(ct):
                total_cleared += 1
        
        return {
            "success": True,
            "message": f"Cache {cache_type} limpo com sucesso",
            "cache_types_cleared": total_cleared
        }
        
    except Exception as e:
        logger.error(f"Erro ao limpar cache {cache_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao limpar cache: {str(e)}")


@router.get("/performance/report", response_model=PerformanceReportResponse)
async def get_performance_report():
    """Obtém relatório de performance"""
    try:
        report = performance_optimizer.get_performance_report()
        
        return PerformanceReportResponse(
            success=True,
            report=report,
            timestamp=report.get('timestamp', '')
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter relatório de performance: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter relatório: {str(e)}")


@router.post("/performance/analyze", response_model=OptimizationTaskResponse)
async def analyze_performance(background_tasks: BackgroundTasks):
    """Executa análise de performance em background"""
    try:
        task = analyze_performance_task.delay()
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message="Análise de performance agendada",
            task_type="performance_analysis"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar análise de performance: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar análise: {str(e)}")


@router.post("/database/optimize", response_model=DatabaseOptimizationResponse)
async def optimize_database(background_tasks: BackgroundTasks):
    """Executa otimização do banco de dados em background"""
    try:
        task = optimize_database_task.delay()
        
        return DatabaseOptimizationResponse(
            success=True,
            task_id=task.id,
            message="Otimização do banco de dados agendada",
            task_type="database_optimization"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar otimização do banco: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar otimização: {str(e)}")


@router.get("/database/recommendations")
async def get_database_recommendations():
    """Obtém recomendações de otimização do banco de dados"""
    try:
        recommendations = performance_optimizer.optimize_database_queries()
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "index_recommendations": len([r for r in recommendations if r.get('type') == 'index'])
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter recomendações do banco: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter recomendações: {str(e)}")


@router.post("/compression/compress", response_model=CompressionResponse)
async def compress_data(request: CompressionRequest):
    """Comprime dados usando o algoritmo especificado"""
    try:
        compressed_data = compression_service.compress_data(
            data=request.data,
            algorithm=request.algorithm,
            level=request.level
        )
        
        return CompressionResponse(
            success=True,
            compressed_data=compressed_data,
            algorithm=request.algorithm or 'gzip',
            compression_ratio=compressed_data.get('compression_ratio', 0)
        )
        
    except Exception as e:
        logger.error(f"Erro ao comprimir dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao comprimir dados: {str(e)}")


@router.post("/compression/decompress")
async def decompress_data(compressed_info: Dict[str, Any]):
    """Descomprime dados"""
    try:
        decompressed_data = compression_service.decompress_data(compressed_info)
        
        return {
            "success": True,
            "decompressed_data": decompressed_data,
            "algorithm": compressed_info.get('algorithm'),
            "original_size": compressed_info.get('original_size')
        }
        
    except Exception as e:
        logger.error(f"Erro ao descomprimir dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao descomprimir dados: {str(e)}")


@router.post("/compression/compress-old-data", response_model=OptimizationTaskResponse)
async def compress_old_data(
    days_old: int = 30,
    algorithm: str = "gzip",
    background_tasks: BackgroundTasks = None
):
    """Comprime dados antigos em background"""
    try:
        task = compress_old_data_task.delay(days_old=days_old, algorithm=algorithm)
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message=f"Compressão de dados antigos agendada (>{days_old} dias)",
            task_type="data_compression",
            parameters={"days_old": days_old, "algorithm": algorithm}
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar compressão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar compressão: {str(e)}")


@router.post("/compression/cleanup", response_model=OptimizationTaskResponse)
async def cleanup_compressed_files(
    older_than_days: int = 90,
    background_tasks: BackgroundTasks = None
):
    """Remove arquivos comprimidos antigos em background"""
    try:
        task = cleanup_compressed_files_task.delay(older_than_days=older_than_days)
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message=f"Limpeza de arquivos comprimidos agendada (>{older_than_days} dias)",
            task_type="compressed_files_cleanup",
            parameters={"older_than_days": older_than_days}
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar limpeza: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar limpeza: {str(e)}")


@router.get("/compression/stats")
async def get_compression_stats(data: Dict[str, Any]):
    """Compara diferentes algoritmos de compressão"""
    try:
        stats = compression_service.get_compression_stats(data)
        
        return {
            "success": True,
            "compression_stats": stats,
            "best_algorithm": stats.get('best_algorithm'),
            "best_ratio": stats.get('best_ratio')
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de compressão: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/memory/usage", response_model=MemoryUsageResponse)
async def get_memory_usage():
    """Obtém informações de uso de memória"""
    try:
        memory_stats = performance_optimizer.optimize_memory_usage()
        
        return MemoryUsageResponse(
            success=True,
            memory_stats=memory_stats,
            system_memory_percent=memory_stats.get('system_memory', {}).get('percent', 0)
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter uso de memória: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter uso de memória: {str(e)}")


@router.post("/cache/health-check", response_model=OptimizationTaskResponse)
async def check_cache_health(background_tasks: BackgroundTasks):
    """Executa verificação de saúde do cache em background"""
    try:
        task = monitor_cache_health_task.delay()
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message="Verificação de saúde do cache agendada",
            task_type="cache_health_check"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar verificação de cache: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar verificação: {str(e)}")


@router.post("/cache/optimize-analytics", response_model=OptimizationTaskResponse)
async def optimize_analytics_cache(background_tasks: BackgroundTasks):
    """Otimiza cache de analytics em background"""
    try:
        task = optimize_analytics_cache_task.delay()
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message="Otimização do cache de analytics agendada",
            task_type="analytics_cache_optimization"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar otimização de analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar otimização: {str(e)}")


@router.post("/report/generate", response_model=OptimizationTaskResponse)
async def generate_optimization_report(background_tasks: BackgroundTasks):
    """Gera relatório de otimização em background"""
    try:
        task = generate_optimization_report_task.delay()
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message="Geração de relatório de otimização agendada",
            task_type="optimization_report"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar relatório: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar relatório: {str(e)}")


@router.get("/status", response_model=OptimizationStatusResponse)
async def get_optimization_status():
    """Obtém status atual das otimizações"""
    try:
        status = performance_optimizer.get_optimization_status()
        
        # Adiciona informações de cache
        cache_healthy = redis_cache.ping()
        cache_stats = redis_cache.get_stats()
        
        status.update({
            'cache_healthy': cache_healthy,
            'cache_hit_rate': cache_stats.get('hit_rate', 0),
            'cache_memory_usage': redis_cache.get_memory_usage()
        })
        
        return OptimizationStatusResponse(
            success=True,
            status=status,
            timestamp=status.get('last_optimization', '')
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter status de otimização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")


@router.post("/maintenance/daily", response_model=OptimizationTaskResponse)
async def run_daily_maintenance(background_tasks: BackgroundTasks):
    """Executa manutenção diária em background"""
    try:
        task = daily_maintenance_task.delay()
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message="Manutenção diária agendada",
            task_type="daily_maintenance"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar manutenção diária: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar manutenção: {str(e)}")


@router.post("/maintenance/weekly", response_model=OptimizationTaskResponse)
async def run_weekly_maintenance(background_tasks: BackgroundTasks):
    """Executa manutenção semanal em background"""
    try:
        task = weekly_maintenance_task.delay()
        
        return OptimizationTaskResponse(
            success=True,
            task_id=task.id,
            message="Manutenção semanal agendada",
            task_type="weekly_maintenance"
        )
        
    except Exception as e:
        logger.error(f"Erro ao agendar manutenção semanal: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao agendar manutenção: {str(e)}")


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Obtém status de uma tarefa de otimização"""
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "success": result.successful() if result.ready() else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter status da tarefa {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")


@router.get("/health")
async def optimization_health_check():
    """Health check para serviços de otimização"""
    try:
        # Verifica cache
        cache_healthy = redis_cache.ping()
        
        # Verifica otimizador
        optimizer_status = performance_optimizer.get_optimization_status()
        
        # Verifica compressão
        compression_available = True  # Sempre disponível (bibliotecas padrão)
        
        overall_health = cache_healthy and optimizer_status.get('database_optimized', False)
        
        return {
            "overall_health": overall_health,
            "cache_healthy": cache_healthy,
            "optimizer_healthy": optimizer_status.get('database_optimized', False),
            "compression_available": compression_available,
            "timestamp": optimizer_status.get('last_optimization', '')
        }
        
    except Exception as e:
        logger.error(f"Erro no health check de otimização: {e}")
        return {
            "overall_health": False,
            "error": str(e)
        } 