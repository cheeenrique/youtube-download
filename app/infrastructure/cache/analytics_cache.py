from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import json
import logging

from .redis_cache import redis_cache

logger = logging.getLogger(__name__)


class AnalyticsCache:
    """Sistema de cache especializado para analytics e relatórios"""
    
    # Tempos de cache em segundos
    CACHE_TTL = {
        'dashboard': 300,        # 5 minutos
        'stats': 600,            # 10 minutos
        'reports': 3600,         # 1 hora
        'popular_videos': 1800,  # 30 minutos
        'user_activity': 900,    # 15 minutos
        'error_analytics': 1200, # 20 minutos
        'performance': 300,      # 5 minutos
        'system_metrics': 60,    # 1 minuto
        'logs': 300,             # 5 minutos
        'audit_trail': 1800      # 30 minutos
    }
    
    def __init__(self):
        self.cache = redis_cache
    
    def _generate_cache_key(self, cache_type: str, params: Dict[str, Any]) -> str:
        """Gera chave de cache baseada no tipo e parâmetros"""
        # Ordena parâmetros para consistência
        sorted_params = dict(sorted(params.items()))
        params_str = json.dumps(sorted_params, sort_keys=True)
        
        # Gera hash para chave mais curta
        hash_obj = hashlib.md5(params_str.encode())
        return f"{cache_type}_{hash_obj.hexdigest()}"
    
    def _get_cache_ttl(self, cache_type: str) -> int:
        """Obtém TTL para um tipo de cache"""
        return self.CACHE_TTL.get(cache_type, 300)
    
    # Dashboard e Métricas Gerais
    def cache_dashboard(self, data: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Cache do dashboard principal"""
        cache_key = self._generate_cache_key('dashboard', {'user_id': user_id})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('dashboard'))
    
    def get_cached_dashboard(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtém dashboard do cache"""
        cache_key = self._generate_cache_key('dashboard', {'user_id': user_id})
        return self.cache.get('analytics', cache_key)
    
    def cache_metrics_summary(self, data: Dict[str, Any]) -> bool:
        """Cache das métricas resumidas"""
        cache_key = self._generate_cache_key('metrics_summary', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('stats'))
    
    def get_cached_metrics_summary(self) -> Optional[Dict[str, Any]]:
        """Obtém métricas resumidas do cache"""
        cache_key = self._generate_cache_key('metrics_summary', {})
        return self.cache.get('analytics', cache_key)
    
    def cache_realtime_metrics(self, data: Dict[str, Any]) -> bool:
        """Cache das métricas em tempo real"""
        cache_key = self._generate_cache_key('realtime_metrics', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('system_metrics'))
    
    def get_cached_realtime_metrics(self) -> Optional[Dict[str, Any]]:
        """Obtém métricas em tempo real do cache"""
        cache_key = self._generate_cache_key('realtime_metrics', {})
        return self.cache.get('analytics', cache_key)
    
    # Estatísticas Específicas
    def cache_download_stats(self, data: Dict[str, Any], period: str = 'all') -> bool:
        """Cache das estatísticas de downloads"""
        cache_key = self._generate_cache_key('download_stats', {'period': period})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('stats'))
    
    def get_cached_download_stats(self, period: str = 'all') -> Optional[Dict[str, Any]]:
        """Obtém estatísticas de downloads do cache"""
        cache_key = self._generate_cache_key('download_stats', {'period': period})
        return self.cache.get('analytics', cache_key)
    
    def cache_performance_metrics(self, data: Dict[str, Any], period: str = 'all') -> bool:
        """Cache das métricas de performance"""
        cache_key = self._generate_cache_key('performance_metrics', {'period': period})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('performance'))
    
    def get_cached_performance_metrics(self, period: str = 'all') -> Optional[Dict[str, Any]]:
        """Obtém métricas de performance do cache"""
        cache_key = self._generate_cache_key('performance_metrics', {'period': period})
        return self.cache.get('analytics', cache_key)
    
    def cache_error_analytics(self, data: Dict[str, Any], period: str = 'all') -> bool:
        """Cache das análises de erro"""
        cache_key = self._generate_cache_key('error_analytics', {'period': period})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('error_analytics'))
    
    def get_cached_error_analytics(self, period: str = 'all') -> Optional[Dict[str, Any]]:
        """Obtém análises de erro do cache"""
        cache_key = self._generate_cache_key('error_analytics', {'period': period})
        return self.cache.get('analytics', cache_key)
    
    def cache_user_activity(self, data: Dict[str, Any], period: str = 'all') -> bool:
        """Cache da atividade de usuários"""
        cache_key = self._generate_cache_key('user_activity', {'period': period})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('user_activity'))
    
    def get_cached_user_activity(self, period: str = 'all') -> Optional[Dict[str, Any]]:
        """Obtém atividade de usuários do cache"""
        cache_key = self._generate_cache_key('user_activity', {'period': period})
        return self.cache.get('analytics', cache_key)
    
    def cache_popular_videos(self, data: List[Dict[str, Any]], limit: int = 10) -> bool:
        """Cache dos vídeos mais populares"""
        cache_key = self._generate_cache_key('popular_videos', {'limit': limit})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('popular_videos'))
    
    def get_cached_popular_videos(self, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Obtém vídeos populares do cache"""
        cache_key = self._generate_cache_key('popular_videos', {'limit': limit})
        return self.cache.get('analytics', cache_key)
    
    def cache_quality_preferences(self, data: Dict[str, Any]) -> bool:
        """Cache das preferências de qualidade"""
        cache_key = self._generate_cache_key('quality_preferences', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('stats'))
    
    def get_cached_quality_preferences(self) -> Optional[Dict[str, Any]]:
        """Obtém preferências de qualidade do cache"""
        cache_key = self._generate_cache_key('quality_preferences', {})
        return self.cache.get('analytics', cache_key)
    
    def cache_format_usage(self, data: Dict[str, Any]) -> bool:
        """Cache do uso de formatos"""
        cache_key = self._generate_cache_key('format_usage', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('stats'))
    
    def get_cached_format_usage(self) -> Optional[Dict[str, Any]]:
        """Obtém uso de formatos do cache"""
        cache_key = self._generate_cache_key('format_usage', {})
        return self.cache.get('analytics', cache_key)
    
    def cache_google_drive_stats(self, data: Dict[str, Any]) -> bool:
        """Cache das estatísticas do Google Drive"""
        cache_key = self._generate_cache_key('google_drive_stats', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('stats'))
    
    def get_cached_google_drive_stats(self) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas do Google Drive do cache"""
        cache_key = self._generate_cache_key('google_drive_stats', {})
        return self.cache.get('analytics', cache_key)
    
    def cache_temporary_url_stats(self, data: Dict[str, Any]) -> bool:
        """Cache das estatísticas de URLs temporárias"""
        cache_key = self._generate_cache_key('temporary_url_stats', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('stats'))
    
    def get_cached_temporary_url_stats(self) -> Optional[Dict[str, Any]]:
        """Obtém estatísticas de URLs temporárias do cache"""
        cache_key = self._generate_cache_key('temporary_url_stats', {})
        return self.cache.get('analytics', cache_key)
    
    def cache_system_metrics(self, data: Dict[str, Any]) -> bool:
        """Cache das métricas do sistema"""
        cache_key = self._generate_cache_key('system_metrics', {})
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('system_metrics'))
    
    def get_cached_system_metrics(self) -> Optional[Dict[str, Any]]:
        """Obtém métricas do sistema do cache"""
        cache_key = self._generate_cache_key('system_metrics', {})
        return self.cache.get('analytics', cache_key)
    
    # Logs e Auditoria
    def cache_logs(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> bool:
        """Cache dos logs de downloads"""
        cache_key = self._generate_cache_key('logs', filters)
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('logs'))
    
    def get_cached_logs(self, filters: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Obtém logs do cache"""
        cache_key = self._generate_cache_key('logs', filters)
        return self.cache.get('analytics', cache_key)
    
    def cache_audit_trail(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> bool:
        """Cache da trilha de auditoria"""
        cache_key = self._generate_cache_key('audit_trail', filters)
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('audit_trail'))
    
    def get_cached_audit_trail(self, filters: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Obtém trilha de auditoria do cache"""
        cache_key = self._generate_cache_key('audit_trail', filters)
        return self.cache.get('analytics', cache_key)
    
    # Relatórios
    def cache_report(self, report_type: str, data: Dict[str, Any], params: Dict[str, Any]) -> bool:
        """Cache de relatórios"""
        cache_key = self._generate_cache_key(f'report_{report_type}', params)
        return self.cache.set('analytics', cache_key, data, self._get_cache_ttl('reports'))
    
    def get_cached_report(self, report_type: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtém relatório do cache"""
        cache_key = self._generate_cache_key(f'report_{report_type}', params)
        return self.cache.get('analytics', cache_key)
    
    # Cache Inteligente com Invalidação
    def invalidate_dashboard_cache(self) -> bool:
        """Invalida cache do dashboard"""
        return self.cache.clear_prefix('analytics')
    
    def invalidate_stats_cache(self) -> bool:
        """Invalida cache de estatísticas"""
        patterns = [
            'download_stats_*',
            'performance_metrics_*',
            'error_analytics_*',
            'user_activity_*',
            'popular_videos_*',
            'quality_preferences_*',
            'format_usage_*',
            'google_drive_stats_*',
            'temporary_url_stats_*',
            'system_metrics_*'
        ]
        
        success = True
        for pattern in patterns:
            keys = self.cache.get_keys('analytics', pattern)
            for key in keys:
                if not self.cache.delete('analytics', key):
                    success = False
        
        return success
    
    def invalidate_logs_cache(self) -> bool:
        """Invalida cache de logs"""
        patterns = ['logs_*', 'audit_trail_*']
        
        success = True
        for pattern in patterns:
            keys = self.cache.get_keys('analytics', pattern)
            for key in keys:
                if not self.cache.delete('analytics', key):
                    success = False
        
        return success
    
    def invalidate_reports_cache(self) -> bool:
        """Invalida cache de relatórios"""
        pattern = 'report_*'
        keys = self.cache.get_keys('analytics', pattern)
        
        success = True
        for key in keys:
            if not self.cache.delete('analytics', key):
                success = False
        
        return success
    
    # Cache de Contadores
    def increment_download_counter(self, period: str = 'daily') -> Optional[int]:
        """Incrementa contador de downloads"""
        key = f'download_counter_{period}_{datetime.now().strftime("%Y-%m-%d")}'
        return self.cache.increment('analytics', key)
    
    def get_download_counter(self, period: str = 'daily') -> Optional[int]:
        """Obtém contador de downloads"""
        key = f'download_counter_{period}_{datetime.now().strftime("%Y-%m-%d")}'
        return self.cache.get('analytics', key)
    
    def increment_error_counter(self, error_type: str) -> Optional[int]:
        """Incrementa contador de erros"""
        key = f'error_counter_{error_type}_{datetime.now().strftime("%Y-%m-%d")}'
        return self.cache.increment('analytics', key)
    
    def get_error_counter(self, error_type: str) -> Optional[int]:
        """Obtém contador de erros"""
        key = f'error_counter_{error_type}_{datetime.now().strftime("%Y-%m-%d")}'
        return self.cache.get('analytics', key)
    
    # Cache de Sessões de Usuário
    def cache_user_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """Cache de sessão de usuário"""
        key = f'user_session_{user_id}'
        return self.cache.set('analytics', key, session_data, 3600)  # 1 hora
    
    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém sessão de usuário do cache"""
        key = f'user_session_{user_id}'
        return self.cache.get('analytics', key)
    
    def delete_user_session(self, user_id: str) -> bool:
        """Remove sessão de usuário do cache"""
        key = f'user_session_{user_id}'
        return self.cache.delete('analytics', key)
    
    # Cache de Configurações
    def cache_analytics_config(self, config: Dict[str, Any]) -> bool:
        """Cache de configurações de analytics"""
        return self.cache.set('analytics', 'config', config, 86400)  # 24 horas
    
    def get_analytics_config(self) -> Optional[Dict[str, Any]]:
        """Obtém configurações de analytics do cache"""
        return self.cache.get('analytics', 'config')
    
    # Limpeza Automática
    def cleanup_expired_cache(self) -> bool:
        """Limpa cache expirado (Redis faz automaticamente, mas pode ser útil)"""
        try:
            # Redis faz limpeza automática baseada no TTL
            # Este método pode ser usado para limpeza manual se necessário
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache expirado: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache de analytics"""
        try:
            # Obtém todas as chaves de analytics
            keys = self.cache.get_keys('analytics', '*')
            
            stats = {
                'total_keys': len(keys),
                'cache_types': {},
                'memory_usage': self.cache.get_memory_usage(),
                'redis_stats': self.cache.get_stats()
            }
            
            # Agrupa chaves por tipo
            for key in keys:
                cache_type = key.split('_')[0] if '_' in key else 'other'
                stats['cache_types'][cache_type] = stats['cache_types'].get(cache_type, 0) + 1
            
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {e}")
            return {}


# Instância global do cache de analytics
analytics_cache = AnalyticsCache() 