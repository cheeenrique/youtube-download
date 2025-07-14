from celery import shared_task
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import os

from app.shared.config import settings
from app.infrastructure.cache.mock_cache import mock_cache as redis_cache
from app.infrastructure.cache.analytics_cache import analytics_cache
from app.infrastructure.optimization.performance_optimizer import performance_optimizer
from app.infrastructure.optimization.compression_service import compression_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="optimization.cleanup_cache")
def cleanup_cache_task(self, cache_type: str = "all", older_than_hours: int = 24):
    """Tarefa para limpeza de cache"""
    try:
        logger.info(f"Iniciando limpeza de cache: {cache_type}")
        
        if cache_type == "all":
            # Limpa todos os tipos de cache
            cache_types = ['analytics', 'download', 'user', 'stats', 'reports', 'temp_url', 'drive', 'system']
        else:
            cache_types = [cache_type]
        
        total_cleaned = 0
        
        for ct in cache_types:
            try:
                # Obtém chaves antigas
                keys = redis_cache.get_keys(ct, "*")
                cleaned_count = 0
                
                for key in keys:
                    # Verifica TTL da chave
                    ttl = redis_cache.ttl(ct, key)
                    if ttl > 0 and ttl < (older_than_hours * 3600):
                        if redis_cache.delete(ct, key):
                            cleaned_count += 1
                
                total_cleaned += cleaned_count
                logger.info(f"Cache {ct}: {cleaned_count} chaves removidas")
                
            except Exception as e:
                logger.error(f"Erro ao limpar cache {ct}: {e}")
        
        logger.info(f"Limpeza de cache concluída. Total: {total_cleaned} chaves removidas")
        
        return {
            'success': True,
            'cache_type': cache_type,
            'total_cleaned': total_cleaned,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na tarefa de limpeza de cache: {e}")
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, name="optimization.analyze_performance")
def analyze_performance_task(self):
    """Tarefa para análise de performance"""
    try:
        logger.info("Iniciando análise de performance")
        
        # Gera relatório de performance
        performance_report = performance_optimizer.get_performance_report()
        
        # Armazena relatório no cache
        analytics_cache.cache_report('performance_analysis', performance_report, {})
        
        # Verifica se há recomendações críticas
        critical_recommendations = [
            rec for rec in performance_report.get('recommendations', [])
            if any(keyword in rec.lower() for keyword in ['crítico', 'alto', 'muitas'])
        ]
        
        if critical_recommendations:
            logger.warning(f"Recomendações críticas de performance: {critical_recommendations}")
        
        logger.info("Análise de performance concluída")
        
        return {
            'success': True,
            'report': performance_report,
            'critical_recommendations': len(critical_recommendations),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na tarefa de análise de performance: {e}")
        raise self.retry(countdown=300, max_retries=3)


@shared_task(bind=True, name="optimization.optimize_database")
def optimize_database_task(self):
    """Tarefa para otimização do banco de dados"""
    try:
        logger.info("Iniciando otimização do banco de dados")
        
        # Analisa queries e gera recomendações
        recommendations = performance_optimizer.optimize_database_queries()
        
        # Cria índices recomendados (apenas os mais importantes)
        important_recommendations = [
            rec for rec in recommendations
            if rec.get('type') == 'index' and 'alta cardinalidade' in rec.get('reason', '')
        ][:5]  # Limita a 5 índices por vez
        
        if important_recommendations:
            creation_results = performance_optimizer.create_recommended_indexes(important_recommendations)
            logger.info(f"Índices criados: {creation_results['created']}, Falharam: {creation_results['failed']}")
        else:
            creation_results = {'created': 0, 'failed': 0, 'errors': []}
        
        # Otimiza pool de conexões
        pool_stats = performance_optimizer.optimize_connection_pool()
        
        logger.info("Otimização do banco de dados concluída")
        
        return {
            'success': True,
            'recommendations_generated': len(recommendations),
            'indexes_created': creation_results['created'],
            'indexes_failed': creation_results['failed'],
            'pool_stats': pool_stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na tarefa de otimização do banco: {e}")
        raise self.retry(countdown=600, max_retries=2)


@shared_task(bind=True, name="optimization.compress_old_data")
def compress_old_data_task(self, days_old: int = 30, algorithm: str = "gzip"):
    """Tarefa para compressão de dados antigos"""
    try:
        logger.info(f"Iniciando compressão de dados antigos (>{days_old} dias)")
        
        # Diretórios para compressão
        directories = [
            settings.reports_dir,
            settings.analytics_data_dir,
            "logs",
            "videos/temp"
        ]
        
        total_compressed = 0
        total_space_saved = 0
        compression_results = []
        
        for directory in directories:
            if not os.path.exists(directory):
                continue
                
            try:
                # Encontra arquivos antigos
                cutoff_date = datetime.now() - timedelta(days=days_old)
                old_files = []
                
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    
                    if os.path.isfile(file_path):
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if file_time < cutoff_date and not any(
                            filename.endswith(ext) for ext in ['.gz', '.zlib', '.bz2', '.xz']
                        ):
                            old_files.append(file_path)
                
                # Comprime arquivos em lote
                if old_files:
                    batch_results = compression_service.batch_compress_files(
                        old_files[:10],  # Limita a 10 arquivos por vez
                        algorithm=algorithm
                    )
                    
                    for result in batch_results:
                        if result.get('success', True) and 'space_saved' in result:
                            total_space_saved += result['space_saved']
                            total_compressed += 1
                    
                    compression_results.extend(batch_results)
                    
                    logger.info(f"Diretório {directory}: {len(batch_results)} arquivos processados")
                
            except Exception as e:
                logger.error(f"Erro ao processar diretório {directory}: {e}")
        
        logger.info(f"Compressão concluída. {total_compressed} arquivos, {total_space_saved} bytes economizados")
        
        return {
            'success': True,
            'total_compressed': total_compressed,
            'total_space_saved': total_space_saved,
            'algorithm': algorithm,
            'results': compression_results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na tarefa de compressão: {e}")
        raise self.retry(countdown=1800, max_retries=2)


@shared_task(bind=True, name="optimization.cleanup_compressed_files")
def cleanup_compressed_files_task(self, older_than_days: int = 90):
    """Tarefa para limpeza de arquivos comprimidos antigos"""
    try:
        logger.info(f"Iniciando limpeza de arquivos comprimidos (>{older_than_days} dias)")
        
        # Diretórios para limpeza
        directories = [
            settings.reports_dir,
            settings.analytics_data_dir,
            "logs",
            "videos/temp"
        ]
        
        total_cleaned = 0
        total_space_freed = 0
        
        for directory in directories:
            if os.path.exists(directory):
                try:
                    cleanup_result = compression_service.cleanup_compressed_files(
                        directory, older_than_days
                    )
                    
                    if 'total_files_removed' in cleanup_result:
                        total_cleaned += cleanup_result['total_files_removed']
                        total_space_freed += cleanup_result.get('total_space_freed', 0)
                        
                        logger.info(f"Diretório {directory}: {cleanup_result['total_files_removed']} arquivos removidos")
                
                except Exception as e:
                    logger.error(f"Erro ao limpar diretório {directory}: {e}")
        
        logger.info(f"Limpeza concluída. {total_cleaned} arquivos removidos, {total_space_freed} bytes liberados")
        
        return {
            'success': True,
            'total_files_removed': total_cleaned,
            'total_space_freed': total_space_freed,
            'older_than_days': older_than_days,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na tarefa de limpeza: {e}")
        raise self.retry(countdown=3600, max_retries=2)


@shared_task(bind=True, name="optimization.monitor_cache_health")
def monitor_cache_health_task(self):
    """Tarefa para monitoramento da saúde do cache"""
    try:
        logger.info("Iniciando monitoramento da saúde do cache")
        
        # Verifica conectividade
        cache_healthy = redis_cache.ping()
        
        if not cache_healthy:
            logger.error("Cache Redis não está respondendo")
            return {
                'success': False,
                'cache_healthy': False,
                'error': 'Cache não está respondendo',
                'timestamp': datetime.now().isoformat()
            }
        
        # Obtém estatísticas do cache
        cache_stats = redis_cache.get_stats()
        memory_usage = redis_cache.get_memory_usage()
        
        # Verifica uso de memória
        memory_percent = (memory_usage.get('used_memory', 0) / 
                         (memory_usage.get('used_memory_peak', 1) or 1)) * 100
        
        # Verifica taxa de hit
        hit_rate = cache_stats.get('hit_rate', 0)
        
        # Gera alertas
        alerts = []
        
        if memory_percent > 80:
            alerts.append(f"Uso de memória alto: {memory_percent:.1f}%")
        
        if hit_rate < 50:
            alerts.append(f"Taxa de hit baixa: {hit_rate:.1f}%")
        
        if cache_stats.get('keyspace_misses', 0) > 1000:
            alerts.append("Muitas falhas de cache detectadas")
        
        # Armazena métricas
        health_metrics = {
            'cache_healthy': cache_healthy,
            'memory_usage': memory_usage,
            'cache_stats': cache_stats,
            'memory_percent': memory_percent,
            'hit_rate': hit_rate,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }
        
        analytics_cache.cache_system_metrics(health_metrics)
        
        logger.info(f"Monitoramento concluído. Alertas: {len(alerts)}")
        
        return {
            'success': True,
            'cache_healthy': cache_healthy,
            'memory_percent': memory_percent,
            'hit_rate': hit_rate,
            'alerts': alerts,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro no monitoramento do cache: {e}")
        raise self.retry(countdown=120, max_retries=3)


@shared_task(bind=True, name="optimization.optimize_analytics_cache")
def optimize_analytics_cache_task(self):
    """Tarefa para otimização do cache de analytics"""
    try:
        logger.info("Iniciando otimização do cache de analytics")
        
        # Obtém estatísticas do cache
        cache_stats = analytics_cache.get_cache_stats()
        
        # Identifica chaves problemáticas
        total_keys = cache_stats.get('total_keys', 0)
        cache_types = cache_stats.get('cache_types', {})
        
        optimization_results = {
            'total_keys_before': total_keys,
            'keys_removed': 0,
            'cache_types_optimized': []
        }
        
        # Otimiza por tipo de cache
        for cache_type, count in cache_types.items():
            if count > 100:  # Muitas chaves de um tipo
                try:
                    # Remove chaves antigas deste tipo
                    keys = redis_cache.get_keys('analytics', f"{cache_type}_*")
                    
                    # Remove 20% das chaves mais antigas
                    keys_to_remove = keys[:int(len(keys) * 0.2)]
                    
                    for key in keys_to_remove:
                        if redis_cache.delete('analytics', key):
                            optimization_results['keys_removed'] += 1
                    
                    optimization_results['cache_types_optimized'].append({
                        'type': cache_type,
                        'keys_before': count,
                        'keys_removed': len(keys_to_remove)
                    })
                    
                    logger.info(f"Cache {cache_type}: {len(keys_to_remove)} chaves removidas")
                
                except Exception as e:
                    logger.error(f"Erro ao otimizar cache {cache_type}: {e}")
        
        # Invalida cache de relatórios antigos
        analytics_cache.invalidate_reports_cache()
        
        logger.info(f"Otimização concluída. {optimization_results['keys_removed']} chaves removidas")
        
        return {
            'success': True,
            'optimization_results': optimization_results,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na otimização do cache de analytics: {e}")
        raise self.retry(countdown=900, max_retries=2)


@shared_task(bind=True, name="optimization.generate_optimization_report")
def generate_optimization_report_task(self):
    """Tarefa para geração de relatório de otimização"""
    try:
        logger.info("Iniciando geração de relatório de otimização")
        
        # Coleta dados de otimização
        performance_report = performance_optimizer.get_performance_report()
        cache_stats = analytics_cache.get_cache_stats()
        memory_stats = performance_optimizer.optimize_memory_usage()
        
        # Gera relatório consolidado
        optimization_report = {
            'timestamp': datetime.now().isoformat(),
            'performance': performance_report,
            'cache': cache_stats,
            'memory': memory_stats,
            'recommendations': self._generate_optimization_recommendations(
                performance_report, cache_stats, memory_stats
            )
        }
        
        # Comprime relatório
        compressed_report = compression_service.compress_report(
            optimization_report, algorithm='gzip'
        )
        
        # Armazena no cache
        analytics_cache.cache_report('optimization', compressed_report, {})
        
        logger.info("Relatório de otimização gerado com sucesso")
        
        return {
            'success': True,
            'report_size': len(str(optimization_report)),
            'compressed_size': compressed_report.get('compressed_size', 0),
            'compression_ratio': compressed_report.get('compression_ratio', 0),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na geração do relatório de otimização: {e}")
        raise self.retry(countdown=1800, max_retries=2)
    
    def _generate_optimization_recommendations(self, performance_report: Dict[str, Any],
                                            cache_stats: Dict[str, Any],
                                            memory_stats: Dict[str, Any]) -> List[str]:
        """Gera recomendações de otimização"""
        recommendations = []
        
        # Recomendações baseadas em performance
        if performance_report.get('performance_metrics', {}).get('avg_execution_time', 0) > 1.0:
            recommendations.append("Considere otimizar queries lentas ou adicionar mais cache")
        
        # Recomendações baseadas em cache
        hit_rate = cache_stats.get('redis_stats', {}).get('hit_rate', 0)
        if hit_rate < 70:
            recommendations.append("Taxa de hit do cache baixa. Revise estratégias de cache")
        
        # Recomendações baseadas em memória
        memory_percent = memory_stats.get('system_memory', {}).get('percent', 0)
        if memory_percent > 80:
            recommendations.append("Uso de memória alto. Considere limpar cache ou otimizar uso")
        
        return recommendations


# Tarefas de manutenção periódica
@shared_task(name="optimization.daily_maintenance")
def daily_maintenance_task():
    """Tarefa de manutenção diária"""
    try:
        logger.info("Iniciando manutenção diária")
        
        # Executa tarefas de manutenção
        tasks = [
            cleanup_cache_task.s(cache_type="all", older_than_hours=24),
            analyze_performance_task.s(),
            monitor_cache_health_task.s(),
            optimize_analytics_cache_task.s()
        ]
        
        # Executa tarefas em paralelo
        from celery import group
        job = group(tasks)
        result = job.apply_async()
        
        logger.info("Manutenção diária agendada")
        
        return {
            'success': True,
            'tasks_scheduled': len(tasks),
            'job_id': result.id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na manutenção diária: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(name="optimization.weekly_maintenance")
def weekly_maintenance_task():
    """Tarefa de manutenção semanal"""
    try:
        logger.info("Iniciando manutenção semanal")
        
        # Executa tarefas de manutenção semanal
        tasks = [
            optimize_database_task.s(),
            compress_old_data_task.s(days_old=30),
            cleanup_compressed_files_task.s(older_than_days=90),
            generate_optimization_report_task.s()
        ]
        
        # Executa tarefas em paralelo
        from celery import group
        job = group(tasks)
        result = job.apply_async()
        
        logger.info("Manutenção semanal agendada")
        
        return {
            'success': True,
            'tasks_scheduled': len(tasks),
            'job_id': result.id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na manutenção semanal: {e}")
        return {'success': False, 'error': str(e)} 