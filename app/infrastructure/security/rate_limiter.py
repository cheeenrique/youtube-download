import time
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    max_requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_size: Optional[int] = None  # For token bucket
    refill_rate: Optional[float] = None  # For token bucket


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None


class RateLimiter:
    def __init__(self):
        self.limits: Dict[str, RateLimitConfig] = {}
        self.stores: Dict[str, Dict[str, List[float]]] = {}
        self.token_buckets: Dict[str, Dict[str, Tuple[float, int]]] = {}
    
    def add_limit(self, name: str, config: RateLimitConfig) -> None:
        """Add a new rate limit configuration"""
        self.limits[name] = config
        self.stores[name] = {}
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.token_buckets[name] = {}
    
    def check_limit(self, limit_name: str, identifier: str) -> RateLimitResult:
        """Check if request is allowed based on rate limit"""
        if limit_name not in self.limits:
            return RateLimitResult(allowed=True, remaining=999, reset_time=time.time())
        
        config = self.limits[limit_name]
        current_time = time.time()
        
        if config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(limit_name, identifier, config, current_time)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(limit_name, identifier, config, current_time)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(limit_name, identifier, config, current_time)
        elif config.strategy == RateLimitStrategy.LEAKY_BUCKET:
            return self._check_leaky_bucket(limit_name, identifier, config, current_time)
        else:
            return RateLimitResult(allowed=True, remaining=999, reset_time=current_time)
    
    def _check_fixed_window(self, limit_name: str, identifier: str, 
                           config: RateLimitConfig, current_time: float) -> RateLimitResult:
        """Fixed window rate limiting"""
        window_start = int(current_time / config.window_seconds) * config.window_seconds
        window_key = f"{identifier}_{window_start}"
        
        if window_key not in self.stores[limit_name]:
            self.stores[limit_name][window_key] = []
        
        request_count = len(self.stores[limit_name][window_key])
        
        if request_count >= config.max_requests:
            reset_time = window_start + config.window_seconds
            retry_after = reset_time - current_time
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after
            )
        
        self.stores[limit_name][window_key].append(current_time)
        return RateLimitResult(
            allowed=True,
            remaining=config.max_requests - request_count - 1,
            reset_time=window_start + config.window_seconds
        )
    
    def _check_sliding_window(self, limit_name: str, identifier: str,
                             config: RateLimitConfig, current_time: float) -> RateLimitResult:
        """Sliding window rate limiting"""
        if identifier not in self.stores[limit_name]:
            self.stores[limit_name][identifier] = []
        
        # Remove old requests outside the window
        cutoff_time = current_time - config.window_seconds
        self.stores[limit_name][identifier] = [
            req_time for req_time in self.stores[limit_name][identifier]
            if req_time > cutoff_time
        ]
        
        request_count = len(self.stores[limit_name][identifier])
        
        if request_count >= config.max_requests:
            # Find the oldest request to calculate retry time
            oldest_request = min(self.stores[limit_name][identifier])
            retry_after = oldest_request + config.window_seconds - current_time
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=oldest_request + config.window_seconds,
                retry_after=retry_after
            )
        
        self.stores[limit_name][identifier].append(current_time)
        return RateLimitResult(
            allowed=True,
            remaining=config.max_requests - request_count - 1,
            reset_time=current_time + config.window_seconds
        )
    
    def _check_token_bucket(self, limit_name: str, identifier: str,
                           config: RateLimitConfig, current_time: float) -> RateLimitResult:
        """Token bucket rate limiting"""
        if identifier not in self.token_buckets[limit_name]:
            self.token_buckets[limit_name][identifier] = (current_time, config.burst_size or config.max_requests)
        
        last_update, tokens = self.token_buckets[limit_name][identifier]
        
        # Refill tokens based on time passed
        time_passed = current_time - last_update
        refill_rate = config.refill_rate or (config.max_requests / config.window_seconds)
        tokens_to_add = time_passed * refill_rate
        max_tokens = config.burst_size or config.max_requests
        
        tokens = min(max_tokens, tokens + tokens_to_add)
        
        if tokens < 1:
            # Calculate when next token will be available
            tokens_needed = 1 - tokens
            time_to_next = tokens_needed / refill_rate
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=current_time + time_to_next,
                retry_after=time_to_next
            )
        
        # Consume token
        tokens -= 1
        self.token_buckets[limit_name][identifier] = (current_time, tokens)
        
        return RateLimitResult(
            allowed=True,
            remaining=int(tokens),
            reset_time=current_time + (1 / refill_rate)
        )
    
    def _check_leaky_bucket(self, limit_name: str, identifier: str,
                           config: RateLimitConfig, current_time: float) -> RateLimitResult:
        """Leaky bucket rate limiting"""
        if identifier not in self.stores[limit_name]:
            self.stores[limit_name][identifier] = []
        
        # Remove processed requests (leak from bucket)
        leak_rate = config.max_requests / config.window_seconds
        time_since_last = current_time - (self.stores[limit_name][identifier][-1] if self.stores[limit_name][identifier] else current_time)
        processed_requests = int(time_since_last * leak_rate)
        
        # Remove processed requests from the front of the queue
        self.stores[limit_name][identifier] = self.stores[limit_name][identifier][processed_requests:]
        
        current_queue_size = len(self.stores[limit_name][identifier])
        max_queue_size = config.max_requests
        
        if current_queue_size >= max_queue_size:
            # Calculate when next request can be processed
            time_to_process = 1 / leak_rate
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=current_time + time_to_process,
                retry_after=time_to_process
            )
        
        # Add request to queue
        self.stores[limit_name][identifier].append(current_time)
        
        return RateLimitResult(
            allowed=True,
            remaining=max_queue_size - current_queue_size - 1,
            reset_time=current_time + (1 / leak_rate)
        )
    
    def get_limit_info(self, limit_name: str, identifier: str) -> Optional[Dict[str, any]]:
        """Get current limit information for an identifier"""
        if limit_name not in self.limits:
            return None
        
        config = self.limits[limit_name]
        current_time = time.time()
        
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            if identifier not in self.token_buckets[limit_name]:
                return {
                    "tokens": config.burst_size or config.max_requests,
                    "max_tokens": config.burst_size or config.max_requests,
                    "refill_rate": config.refill_rate or (config.max_requests / config.window_seconds)
                }
            
            last_update, tokens = self.token_buckets[limit_name][identifier]
            time_passed = current_time - last_update
            refill_rate = config.refill_rate or (config.max_requests / config.window_seconds)
            tokens_to_add = time_passed * refill_rate
            max_tokens = config.burst_size or config.max_requests
            current_tokens = min(max_tokens, tokens + tokens_to_add)
            
            return {
                "tokens": current_tokens,
                "max_tokens": max_tokens,
                "refill_rate": refill_rate
            }
        else:
            if identifier not in self.stores[limit_name]:
                return {
                    "requests": 0,
                    "max_requests": config.max_requests,
                    "window_seconds": config.window_seconds
                }
            
            # Count requests in current window
            cutoff_time = current_time - config.window_seconds
            requests = [
                req_time for req_time in self.stores[limit_name][identifier]
                if req_time > cutoff_time
            ]
            
            return {
                "requests": len(requests),
                "max_requests": config.max_requests,
                "window_seconds": config.window_seconds
            }
    
    def reset_limit(self, limit_name: str, identifier: str) -> bool:
        """Reset rate limit for an identifier"""
        if limit_name not in self.limits:
            return False
        
        if limit_name in self.stores and identifier in self.stores[limit_name]:
            del self.stores[limit_name][identifier]
        
        if limit_name in self.token_buckets and identifier in self.token_buckets[limit_name]:
            del self.token_buckets[limit_name][identifier]
        
        return True
    
    def cleanup_old_data(self, max_age_seconds: int = 3600) -> int:
        """Clean up old rate limit data"""
        current_time = time.time()
        cleaned_count = 0
        
        for limit_name, store in self.stores.items():
            for identifier, requests in list(store.items()):
                # Remove old requests
                original_count = len(requests)
                store[identifier] = [
                    req_time for req_time in requests
                    if current_time - req_time < max_age_seconds
                ]
                
                # Remove empty entries
                if not store[identifier]:
                    del store[identifier]
                    cleaned_count += 1
                else:
                    cleaned_count += original_count - len(store[identifier])
        
        return cleaned_count


# RedisRateLimiter comentado - não usando Redis no deploy
# class RedisRateLimiter(RateLimiter):
#     """Rate limiter that uses Redis for distributed environments"""
#     
#     def __init__(self, redis_client):
#         super().__init__()
#         self.redis = redis_client
#     
#     async def check_limit_async(self, limit_name: str, identifier: str) -> RateLimitResult:
#         """Async version of check_limit using Redis"""
#         if limit_name not in self.limits:
#             return RateLimitResult(allowed=True, remaining=999, reset_time=time.time())
#         
#         config = self.limits[limit_name]
#         current_time = time.time()
#         
#         if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
#             return await self._check_sliding_window_redis(limit_name, identifier, config, current_time)
#         else:
#             # For other strategies, fall back to in-memory implementation
#             return self.check_limit(limit_name, identifier)
#     
#     async def _check_sliding_window_redis(self, limit_name: str, identifier: str,
#                                          config: RateLimitConfig, current_time: float) -> RateLimitResult:
#         """Sliding window rate limiting using Redis"""
#         key = f"rate_limit:{limit_name}:{identifier}"
#         cutoff_time = current_time - config.window_seconds
#         
#         # Use Redis pipeline for atomic operations
#         pipe = self.redis.pipeline()
#         
#         # Remove old requests and add current request
#         pipe.zremrangebyscore(key, 0, cutoff_time)
#         pipe.zadd(key, {str(current_time): current_time})
#         pipe.zcard(key)
#         pipe.expire(key, config.window_seconds)
#         
#         results = await pipe.execute()
#         request_count = results[2]
#         
#         if request_count > config.max_requests:
#             # Get the oldest request to calculate retry time
#             oldest_request = await self.redis.zrange(key, 0, 0, withscores=True)
#             if oldest_request:
#                 oldest_time = oldest_request[0][1]
#                 retry_after = oldest_time + config.window_seconds - current_time
#                 return RateLimitResult(
#                     allowed=False,
#                     remaining=0,
#                     reset_time=oldest_time + config.window_seconds,
#                     retry_after=retry_after
#                 )
#         
#         return RateLimitResult(
#             allowed=request_count <= config.max_requests,
#             remaining=max(0, config.max_requests - request_count),
#             reset_time=current_time + config.window_seconds
#         ) 