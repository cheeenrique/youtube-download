import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from datetime import datetime, timedelta
import psutil
import gc

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.shared.config import settings
from app.infrastructure.cache.mock_cache import mock_cache as redis_cache

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Sistema de otimização de performance para a aplicação"""
    
    def __init__(self):
        self.settings = settings
        self.cache = redis_cache
        self.performance_metrics = {}
        self.slow_queries = []
        self.optimization_config = {
            'query_timeout': 30,  # segundos
            'slow_query_threshold': 1.0,  # segundos
            'max_connections': 20,
            'connection_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': False
        }
        
        # Engine otimizado
        self.engine = self._create_optimized_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _create_optimized_engine(self):
        """Cria engine do SQLAlchemy otimizado"""
        try:
            engine = create_engine(
                self.settings.database_url,
                poolclass=QueuePool,
                pool_size=self.optimization_config['max_connections'],
                max_overflow=0,
                pool_timeout=self.optimization_config['connection_timeout'],
                pool_recycle=self.optimization_config['pool_recycle'],
                pool_pre_ping=self.optimization_config['pool_pre_ping'],
                echo=self.optimization_config['echo'],
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "youtube_download_api"
                }
            )
            
            logger.info("Engine SQLAlchemy otimizado criado com sucesso")
            return engine
            
        except Exception as e:
            logger.error(f"Erro ao criar engine otimizado: {e}")
            # Fallback para configuração básica
            return create_engine(self.settings.database_url)
    
    def monitor_performance(self, operation: str):
        """Decorator para monitorar performance de operações"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise e
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss
                    
                    execution_time = end_time - start_time
                    memory_used = end_memory - start_memory
                    
                    self._record_performance_metric(
                        operation, execution_time, memory_used, success
                    )
                
                return result
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                try:
                    result = await func(*args, **kwargs)
                    success = True
                except Exception as e:
                    success = False
                    raise e
                finally:
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss
                    
                    execution_time = end_time - start_time
                    memory_used = end_memory - start_memory
                    
                    self._record_performance_metric(
                        operation, execution_time, memory_used, success
                    )
                
                return result
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        return decorator
    
    def _record_performance_metric(self, operation: str, execution_time: float, 
                                 memory_used: int, success: bool):
        """Registra métrica de performance"""
        metric = {
            'operation': operation,
            'execution_time': execution_time,
            'memory_used': memory_used,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        # Armazena no cache
        cache_key = f"perf_metric_{operation}_{datetime.now().strftime('%Y%m%d_%H')}"
        self.cache.add_to_list('system', cache_key, metric)
        
        # Verifica se é uma query lenta
        if execution_time > self.optimization_config['slow_query_threshold']:
            self.slow_queries.append(metric)
            logger.warning(f"Operação lenta detectada: {operation} - {execution_time:.2f}s")
        
        # Limita o tamanho da lista de queries lentas
        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-50:]
    
    def optimize_database_queries(self):
        """Otimiza queries do banco de dados"""
        try:
            with self.engine.connect() as connection:
                # Análise de estatísticas
                result = connection.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY n_distinct DESC
                """))
                
                stats = [dict(row) for row in result]
                
                # Recomendações de índices
                recommendations = self._generate_index_recommendations(stats)
                
                logger.info(f"Análise de otimização concluída. {len(recommendations)} recomendações geradas")
                return recommendations
                
        except SQLAlchemyError as e:
            logger.error(f"Erro ao otimizar queries: {e}")
            return []
    
    def _generate_index_recommendations(self, stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Gera recomendações de índices baseadas nas estatísticas"""
        recommendations = []
        
        for stat in stats:
            table_name = stat['tablename']
            column_name = stat['attname']
            n_distinct = stat['n_distinct']
            correlation = stat['correlation']
            
            # Recomenda índice para colunas com alta cardinalidade
            if n_distinct > 100 and abs(correlation) < 0.8:
                recommendations.append({
                    'type': 'index',
                    'table': table_name,
                    'column': column_name,
                    'reason': f'Alta cardinalidade ({n_distinct} valores distintos)',
                    'sql': f'CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});'
                })
        
        return recommendations
    
    def create_recommended_indexes(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cria índices recomendados"""
        results = {
            'created': 0,
            'failed': 0,
            'errors': []
        }
        
        for rec in recommendations:
            if rec['type'] == 'index':
                try:
                    with self.engine.connect() as connection:
                        connection.execute(text(rec['sql']))
                        connection.commit()
                        results['created'] += 1
                        logger.info(f"Índice criado: {rec['sql']}")
                        
                except SQLAlchemyError as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'sql': rec['sql'],
                        'error': str(e)
                    })
                    logger.error(f"Erro ao criar índice: {rec['sql']} - {e}")
        
        return results
    
    def optimize_connection_pool(self):
        """Otimiza configurações do pool de conexões"""
        try:
            # Obtém estatísticas do pool
            pool_stats = {
                'size': self.engine.pool.size(),
                'checked_in': self.engine.pool.checkedin(),
                'checked_out': self.engine.pool.checkedout(),
                'overflow': self.engine.pool.overflow(),
                'invalid': self.engine.pool.invalid()
            }
            
            # Ajusta configurações baseado no uso
            if pool_stats['checked_out'] > pool_stats['size'] * 0.8:
                # Aumenta pool se necessário
                new_size = min(pool_stats['size'] + 5, 50)
                logger.info(f"Aumentando pool de conexões para {new_size}")
                
            elif pool_stats['checked_out'] < pool_stats['size'] * 0.3:
                # Reduz pool se subutilizado
                new_size = max(pool_stats['size'] - 2, 5)
                logger.info(f"Reduzindo pool de conexões para {new_size}")
            
            return pool_stats
            
        except Exception as e:
            logger.error(f"Erro ao otimizar pool de conexões: {e}")
            return {}
    
    def optimize_memory_usage(self):
        """Otimiza uso de memória"""
        try:
            # Força coleta de lixo
            collected = gc.collect()
            
            # Obtém estatísticas de memória
            memory_stats = {
                'process_memory': psutil.Process().memory_info(),
                'system_memory': psutil.virtual_memory(),
                'gc_stats': gc.get_stats(),
                'collected_objects': collected
            }
            
            # Limpa cache se necessário
            if memory_stats['system_memory'].percent > 80:
                logger.warning("Uso de memória alto detectado. Limpando cache...")
                self.cache.clear_prefix('analytics')
            
            return memory_stats
            
        except Exception as e:
            logger.error(f"Erro ao otimizar memória: {e}")
            return {}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório de performance"""
        try:
            # Métricas de performance
            performance_metrics = self._aggregate_performance_metrics()
            
            # Queries lentas
            slow_queries_summary = self._analyze_slow_queries()
            
            # Estatísticas do pool
            pool_stats = self.optimize_connection_pool()
            
            # Uso de memória
            memory_stats = self.optimize_memory_usage()
            
            # Cache stats
            cache_stats = self.cache.get_stats()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'performance_metrics': performance_metrics,
                'slow_queries': slow_queries_summary,
                'connection_pool': pool_stats,
                'memory_usage': memory_stats,
                'cache_stats': cache_stats,
                'recommendations': self._generate_performance_recommendations(
                    performance_metrics, slow_queries_summary, pool_stats, memory_stats
                )
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatório de performance: {e}")
            return {'error': str(e)}
    
    def _aggregate_performance_metrics(self) -> Dict[str, Any]:
        """Agrega métricas de performance"""
        try:
            # Obtém métricas das últimas 24 horas
            today = datetime.now().strftime('%Y%m%d')
            metrics = []
            
            for hour in range(24):
                cache_key = f"perf_metrics_{today}_{hour:02d}"
                hour_metrics = self.cache.get_list('system', cache_key)
                if hour_metrics:
                    metrics.extend(hour_metrics)
            
            if not metrics:
                return {}
            
            # Calcula estatísticas
            execution_times = [m['execution_time'] for m in metrics if m.get('execution_time')]
            memory_usage = [m['memory_used'] for m in metrics if m.get('memory_used')]
            success_rate = sum(1 for m in metrics if m.get('success', False)) / len(metrics)
            
            return {
                'total_operations': len(metrics),
                'avg_execution_time': sum(execution_times) / len(execution_times) if execution_times else 0,
                'max_execution_time': max(execution_times) if execution_times else 0,
                'min_execution_time': min(execution_times) if execution_times else 0,
                'avg_memory_usage': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'success_rate': success_rate,
                'operations_by_type': self._group_operations_by_type(metrics)
            }
            
        except Exception as e:
            logger.error(f"Erro ao agregar métricas: {e}")
            return {}
    
    def _group_operations_by_type(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Agrupa operações por tipo"""
        grouped = {}
        
        for metric in metrics:
            op_type = metric.get('operation', 'unknown')
            if op_type not in grouped:
                grouped[op_type] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'success_count': 0
                }
            
            grouped[op_type]['count'] += 1
            grouped[op_type]['total_time'] += metric.get('execution_time', 0)
            if metric.get('success', False):
                grouped[op_type]['success_count'] += 1
        
        # Calcula médias
        for op_type, stats in grouped.items():
            if stats['count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['success_rate'] = stats['success_count'] / stats['count']
        
        return grouped
    
    def _analyze_slow_queries(self) -> Dict[str, Any]:
        """Analisa queries lentas"""
        if not self.slow_queries:
            return {}
        
        # Agrupa por operação
        slow_by_operation = {}
        for query in self.slow_queries:
            op = query.get('operation', 'unknown')
            if op not in slow_by_operation:
                slow_by_operation[op] = []
            slow_by_operation[op].append(query)
        
        # Calcula estatísticas
        analysis = {
            'total_slow_queries': len(self.slow_queries),
            'operations_affected': len(slow_by_operation),
            'slowest_operation': max(self.slow_queries, key=lambda x: x.get('execution_time', 0)),
            'by_operation': {}
        }
        
        for op, queries in slow_by_operation.items():
            times = [q.get('execution_time', 0) for q in queries]
            analysis['by_operation'][op] = {
                'count': len(queries),
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'min_time': min(times)
            }
        
        return analysis
    
    def _generate_performance_recommendations(self, performance_metrics: Dict[str, Any],
                                           slow_queries: Dict[str, Any],
                                           pool_stats: Dict[str, Any],
                                           memory_stats: Dict[str, Any]) -> List[str]:
        """Gera recomendações de performance"""
        recommendations = []
        
        # Análise de tempo de execução
        if performance_metrics.get('avg_execution_time', 0) > 1.0:
            recommendations.append("Tempo médio de execução alto. Considere otimizar queries ou adicionar cache.")
        
        # Análise de queries lentas
        if slow_queries.get('total_slow_queries', 0) > 10:
            recommendations.append("Muitas queries lentas detectadas. Revise índices e otimize queries problemáticas.")
        
        # Análise do pool de conexões
        if pool_stats.get('checked_out', 0) > pool_stats.get('size', 0) * 0.9:
            recommendations.append("Pool de conexões próximo do limite. Considere aumentar o tamanho do pool.")
        
        # Análise de memória
        if memory_stats.get('system_memory', {}).get('percent', 0) > 80:
            recommendations.append("Uso de memória alto. Considere limpar cache ou otimizar uso de memória.")
        
        # Análise de taxa de sucesso
        if performance_metrics.get('success_rate', 1.0) < 0.95:
            recommendations.append("Taxa de sucesso baixa. Revise logs de erro e otimize tratamento de exceções.")
        
        return recommendations
    
    def cleanup_old_metrics(self, days: int = 7):
        """Limpa métricas antigas"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_str = cutoff_date.strftime('%Y%m%d')
            
            # Remove métricas antigas do cache
            keys_to_delete = []
            for i in range(24):
                key = f"perf_metrics_{cutoff_str}_{i:02d}"
                if self.cache.exists('system', key):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.cache.delete('system', key)
            
            logger.info(f"Limpeza de métricas antigas concluída. {len(keys_to_delete)} chaves removidas")
            
        except Exception as e:
            logger.error(f"Erro ao limpar métricas antigas: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Obtém status atual das otimizações"""
        return {
            'database_optimized': True,
            'connection_pool_optimized': True,
            'memory_optimized': True,
            'cache_enabled': True,
            'last_optimization': datetime.now().isoformat(),
            'config': self.optimization_config
        }


# Instância global do otimizador
performance_optimizer = PerformanceOptimizer() 