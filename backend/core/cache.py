"""
Redis-based caching system with automatic key management and TTL.
"""

import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import redis
from .config import settings
from .logger import logger


class CacheManager:
    """Redis cache manager with automatic serialization."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.redis_client is not None
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            MD5 hash of the combined key
        """
        # Combine all arguments into a string
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        key_string = ":".join(key_parts)
        
        # Generate MD5 hash for consistent key length
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.is_available() or not settings.CACHE_ENABLED:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                logger.debug(f"Cache hit: {key}")
                return json.loads(data)
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (default from settings)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.warning(f"Cache not available for key: {key}")
            return False
        
        if not settings.CACHE_ENABLED:
            logger.warning(f"Cache disabled for key: {key}")
            return False
        
        try:
            ttl = ttl or settings.CACHE_DEFAULT_TTL
            data = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, data)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def delete(self, pattern: str) -> int:
        """
        Delete keys matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "file:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0
        
        try:
            keys = list(self.redis_client.scan_iter(pattern))
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Deleted {count} cache keys matching: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache delete error for pattern {pattern}: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache keys."""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("All cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.is_available():
            return {"status": "unavailable"}
        
        try:
            info = self.redis_client.info("stats")
            return {
                "status": "available",
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
                ) * 100,
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "message": str(e)}


# Global cache manager instance
cache = CacheManager()


def cache_result(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None,
):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_builder: Optional custom key builder function
        
    Example:
        @cache_result(prefix="parsed_file", ttl=3600)
        async def parse_file(file_id: str):
            return expensive_operation(file_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache.generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache.generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


__all__ = ["CacheManager", "cache", "cache_result"]
