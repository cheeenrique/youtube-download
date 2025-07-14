# Arquivo desativado: não usar Redis neste deploy
# Todo o conteúdo foi comentado para evitar importação acidental.
'''
import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError
import logging

from app.shared.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Sistema de cache Redis para otimização de performance"""
    
    def __init__(self):
        self.settings = settings
        self.redis_client = redis.from_url(
            self.settings.redis_url,
            decode_responses=False,  # Para suportar pickle
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Prefixos para diferentes tipos de cache
        self.prefixes = {
            'analytics': 'analytics:',
            'download': 'download:',
            'user': 'user:',
            'stats': 'stats:',
            'reports': 'reports:',
            'temp_url': 'temp_url:',
            'drive': 'drive:',
            'system': 'system:'
        }
    
    def _get_key(self, prefix: str, key: str) -> str:
        """Gera chave com prefixo"""
        return f"{self.prefixes.get(prefix, '')}{key}"
    
    def _serialize(self, data: Any) -> bytes:
        """Serializa dados para armazenamento"""
        try:
            # Tenta JSON primeiro (mais eficiente)
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data, default=str).encode('utf-8')
            else:
                # Usa pickle para objetos complexos
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Erro ao serializar dados: {e}")
            return pickle.dumps(data)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserializa dados do cache"""
        try:
            # Tenta JSON primeiro
            json_data = data.decode('utf-8')
            return json.loads(json_data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                # Usa pickle como fallback
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Erro ao deserializar dados: {e}")
                return None
    
    def set(self, prefix: str, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Define um valor no cache"""
        try:
            cache_key = self._get_key(prefix, key)
            serialized_value = self._serialize(value)
            
            if expire:
                return self.redis_client.setex(cache_key, expire, serialized_value)
            else:
                return self.redis_client.set(cache_key, serialized_value)
        except RedisError as e:
            logger.error(f"Erro ao definir cache {prefix}:{key}: {e}")
            return False
    
    def get(self, prefix: str, key: str) -> Optional[Any]:
        """Obtém um valor do cache"""
        try:
            cache_key = self._get_key(prefix, key)
            data = self.redis_client.get(cache_key)
            
            if data is None:
                return None
            
            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Erro ao obter cache {prefix}:{key}: {e}")
            return None
    
    def delete(self, prefix: str, key: str) -> bool:
        """Remove um valor do cache"""
        try:
            cache_key = self._get_key(prefix, key)
            return bool(self.redis_client.delete(cache_key))
        except RedisError as e:
            logger.error(f"Erro ao deletar cache {prefix}:{key}: {e}")
            return False
    
    def exists(self, prefix: str, key: str) -> bool:
        """Verifica se uma chave existe no cache"""
        try:
            cache_key = self._get_key(prefix, key)
            return bool(self.redis_client.exists(cache_key))
        except RedisError as e:
            logger.error(f"Erro ao verificar cache {prefix}:{key}: {e}")
            return False
    
    def expire(self, prefix: str, key: str, seconds: int) -> bool:
        """Define tempo de expiração para uma chave"""
        try:
            cache_key = self._get_key(prefix, key)
            return bool(self.redis_client.expire(cache_key, seconds))
        except RedisError as e:
            logger.error(f"Erro ao definir expiração {prefix}:{key}: {e}")
            return False
    
    def ttl(self, prefix: str, key: str) -> int:
        """Retorna o tempo restante de vida de uma chave"""
        try:
            cache_key = self._get_key(prefix, key)
            return self.redis_client.ttl(cache_key)
        except RedisError as e:
            logger.error(f"Erro ao obter TTL {prefix}:{key}: {e}")
            return -1
    
    def increment(self, prefix: str, key: str, amount: int = 1) -> Optional[int]:
        """Incrementa um valor numérico"""
        try:
            cache_key = self._get_key(prefix, key)
            return self.redis_client.incr(cache_key, amount)
        except RedisError as e:
            logger.error(f"Erro ao incrementar {prefix}:{key}: {e}")
            return None
    
    def set_hash(self, prefix: str, key: str, field: str, value: Any) -> bool:
        """Define um campo em um hash"""
        try:
            cache_key = self._get_key(prefix, key)
            serialized_value = self._serialize(value)
            return bool(self.redis_client.hset(cache_key, field, serialized_value))
        except RedisError as e:
            logger.error(f"Erro ao definir hash {prefix}:{key}:{field}: {e}")
            return False
    
    def get_hash(self, prefix: str, key: str, field: str) -> Optional[Any]:
        """Obtém um campo de um hash"""
        try:
            cache_key = self._get_key(prefix, key)
            data = self.redis_client.hget(cache_key, field)
            
            if data is None:
                return None
            
            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Erro ao obter hash {prefix}:{key}:{field}: {e}")
            return None
    
    def get_all_hash(self, prefix: str, key: str) -> Optional[Dict[str, Any]]:
        """Obtém todos os campos de um hash"""
        try:
            cache_key = self._get_key(prefix, key)
            data = self.redis_client.hgetall(cache_key)
            
            if not data:
                return None
            
            result = {}
            for field, value in data.items():
                field_str = field.decode('utf-8') if isinstance(field, bytes) else field
                result[field_str] = self._deserialize(value)
            
            return result
        except RedisError as e:
            logger.error(f"Erro ao obter hash completo {prefix}:{key}: {e}")
            return None
    
    def delete_hash_field(self, prefix: str, key: str, field: str) -> bool:
        """Remove um campo de um hash"""
        try:
            cache_key = self._get_key(prefix, key)
            return bool(self.redis_client.hdel(cache_key, field))
        except RedisError as e:
            logger.error(f"Erro ao deletar campo hash {prefix}:{key}:{field}: {e}")
            return False
    
    def set_list(self, prefix: str, key: str, values: List[Any], expire: Optional[int] = None) -> bool:
        """Define uma lista no cache"""
        try:
            cache_key = self._get_key(prefix, key)
            
            # Remove lista existente
            self.redis_client.delete(cache_key)
            
            # Adiciona novos valores
            for value in values:
                serialized_value = self._serialize(value)
                self.redis_client.rpush(cache_key, serialized_value)
            
            # Define expiração se especificada
            if expire:
                self.redis_client.expire(cache_key, expire)
            
            return True
        except RedisError as e:
            logger.error(f"Erro ao definir lista {prefix}:{key}: {e}")
            return False
    
    def get_list(self, prefix: str, key: str, start: int = 0, end: int = -1) -> Optional[List[Any]]:
        """Obtém uma lista do cache"""
        try:
            cache_key = self._get_key(prefix, key)
            data = self.redis_client.lrange(cache_key, start, end)
            
            if not data:
                return None
            
            return [self._deserialize(item) for item in data]
        except RedisError as e:
            logger.error(f"Erro ao obter lista {prefix}:{key}: {e}")
            return None
    
    def add_to_list(self, prefix: str, key: str, value: Any) -> bool:
        """Adiciona um valor ao final de uma lista"""
        try:
            cache_key = self._get_key(prefix, key)
            serialized_value = self._serialize(value)
            return bool(self.redis_client.rpush(cache_key, serialized_value))
        except RedisError as e:
            logger.error(f"Erro ao adicionar à lista {prefix}:{key}: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> bool:
        """Remove todas as chaves com um prefixo específico"""
        try:
            pattern = self._get_key(prefix, "*")
            keys = self.redis_client.keys(pattern)
            
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        except RedisError as e:
            logger.error(f"Erro ao limpar prefixo {prefix}: {e}")
            return False
    
    def get_keys(self, prefix: str, pattern: str = "*") -> List[str]:
        """Obtém todas as chaves com um padrão específico"""
        try:
            full_pattern = self._get_key(prefix, pattern)
            keys = self.redis_client.keys(full_pattern)
            
            # Remove prefixo das chaves retornadas
            prefix_len = len(self.prefixes.get(prefix, ''))
            return [key.decode('utf-8')[prefix_len:] if isinstance(key, bytes) else key[prefix_len:] 
                    for key in keys]
        except RedisError as e:
            logger.error(f"Erro ao obter chaves {prefix}:{pattern}: {e}")
            return []
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Obtém informações de uso de memória do Redis"""
        try:
            info = self.redis_client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'used_memory_rss': info.get('used_memory_rss', 0),
                'used_memory_rss_human': info.get('used_memory_rss_human', '0B'),
                'mem_fragmentation_ratio': info.get('mem_fragmentation_ratio', 0)
            }
        except RedisError as e:
            logger.error(f"Erro ao obter uso de memória: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do Redis"""
        try:
            info = self.redis_client.info()
            return {
                'total_connections_received': info.get('total_connections_received', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'total_net_input_bytes': info.get('total_net_input_bytes', 0),
                'total_net_output_bytes': info.get('total_net_output_bytes', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except RedisError as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calcula a taxa de hit do cache"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return (hits / total) * 100
    
    def ping(self) -> bool:
        """Testa a conectividade com o Redis"""
        try:
            return self.redis_client.ping()
        except RedisError as e:
            logger.error(f"Erro no ping do Redis: {e}")
            return False
    
    def flush_all(self) -> bool:
        """Remove todos os dados do Redis (CUIDADO!)"""
        try:
            return self.redis_client.flushall()
        except RedisError as e:
            logger.error(f"Erro ao limpar Redis: {e}")
            return False
    
    def close(self):
        """Fecha a conexão com o Redis"""
        try:
            self.redis_client.close()
        except RedisError as e:
            logger.error(f"Erro ao fechar conexão Redis: {e}")


# Instância global do cache
redis_cache = RedisCache() 
''' 