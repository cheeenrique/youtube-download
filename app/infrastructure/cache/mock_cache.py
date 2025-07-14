"""
Mock cache para substituir Redis cache quando não disponível
"""
import time
from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class MockCache:
    """Mock cache que simula funcionalidades básicas do Redis"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
        logger.info("MockCache inicializado (substituindo Redis)")
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém um valor do cache"""
        if key in self._cache:
            if key in self._expiry and time.time() > self._expiry[key]:
                # Expirou, remover
                del self._cache[key]
                del self._expiry[key]
                return None
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Define um valor no cache"""
        self._cache[key] = value
        if expire:
            self._expiry[key] = time.time() + expire
        return True
    
    def delete(self, key: str) -> bool:
        """Remove uma chave do cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
        return True
    
    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe"""
        if key in self._cache:
            if key in self._expiry and time.time() > self._expiry[key]:
                # Expirou, remover
                del self._cache[key]
                del self._expiry[key]
                return False
            return True
        return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """Define expiração para uma chave"""
        if key in self._cache:
            self._expiry[key] = time.time() + seconds
            return True
        return False
    
    def ttl(self, key: str) -> int:
        """Retorna o tempo restante de uma chave"""
        if key in self._cache and key in self._expiry:
            remaining = self._expiry[key] - time.time()
            return max(0, int(remaining))
        return -1
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Incrementa um valor numérico"""
        current = self.get(key) or 0
        if isinstance(current, (int, float)):
            new_value = current + amount
            self.set(key, new_value)
            return new_value
        return 0
    
    def decr(self, key: str, amount: int = 1) -> int:
        """Decrementa um valor numérico"""
        return self.incr(key, -amount)
    
    def clear(self) -> bool:
        """Limpa todo o cache"""
        self._cache.clear()
        self._expiry.clear()
        return True
    
    def clear_prefix(self, prefix: str) -> int:
        """Limpa chaves com um prefixo específico"""
        keys_to_delete = [key for key in self._cache.keys() if key.startswith(prefix)]
        for key in keys_to_delete:
            self.delete(key)
        return len(keys_to_delete)
    
    def ping(self) -> bool:
        """Testa a conectividade (sempre retorna True para mock)"""
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return {
            "total_keys": len(self._cache),
            "memory_usage": len(str(self._cache)),
            "expired_keys": len([k for k, v in self._expiry.items() if time.time() > v]),
            "cache_type": "mock"
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Retorna uso de memória"""
        return {
            "used_memory": len(str(self._cache)),
            "used_memory_human": f"{len(str(self._cache))} bytes",
            "max_memory": "unlimited",
            "max_memory_human": "unlimited"
        }
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Retorna chaves que correspondem ao padrão"""
        # Implementação simples de padrão
        if pattern == "*":
            return list(self._cache.keys())
        elif pattern.endswith("*"):
            prefix = pattern[:-1]
            return [key for key in self._cache.keys() if key.startswith(prefix)]
        else:
            return [key for key in self._cache.keys() if key == pattern]


# Instância global do mock cache
mock_cache = MockCache() 