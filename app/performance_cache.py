"""
Authored by: Performance Engineer (chacha)
Date: 2025-08-05

Performance Cache System

High-performance in-memory caching with TTL, request coalescing, and metrics collection.
Provides Redis-like functionality using Python data structures for local-first architecture.
"""

import time
import threading
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import weakref
from collections import OrderedDict
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"
    TTL_ONLY = "ttl_only"
    LFU = "lfu"

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1

@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expired_entries: int = 0
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_bytes: int = 0
    hit_rate: float = 0.0
    
    def update_hit_rate(self):
        """Update calculated hit rate."""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests * 100
        else:
            self.hit_rate = 0.0

class RequestCoalescer:
    """Request coalescing for duplicate queries."""
    
    def __init__(self):
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
    
    async def coalesce_request(self, key: str, request_func: Callable) -> Any:
        """Coalesce duplicate requests to reduce load."""
        async with self._lock:
            # Check if request is already in progress
            if key in self._pending_requests:
                logger.debug(f"Coalescing request for key: {key[:50]}...")
                return await self._pending_requests[key]
            
            # Create future for this request
            future = asyncio.create_task(request_func())
            self._pending_requests[key] = future
        
        try:
            result = await future
            return result
        finally:
            # Clean up completed request
            async with self._lock:
                self._pending_requests.pop(key, None)

class PerformanceCache:
    """
    High-performance in-memory cache with TTL, LRU eviction, and metrics.
    Optimized for RAG system query caching with request coalescing.
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: float = 300.0,  # 5 minutes
                 cleanup_interval: float = 60.0,  # 1 minute
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 max_memory_mb: int = 100):
        """
        Initialize performance cache.
        
        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
            cleanup_interval: Cleanup interval in seconds
            strategy: Cache eviction strategy
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # Storage
        if strategy == CacheStrategy.LRU:
            self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        else:
            self._cache: Dict[str, CacheEntry] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Metrics
        self.metrics = CacheMetrics()
        
        # Request coalescing
        self.coalescer = RequestCoalescer()
        
        # Cleanup thread
        self._cleanup_thread = None
        self._shutdown_event = threading.Event()
        self._start_cleanup_thread(cleanup_interval)
        
        logger.info(f"Performance cache initialized: max_size={max_size}, "
                   f"ttl={default_ttl}s, strategy={strategy.value}")
    
    def _start_cleanup_thread(self, interval: float):
        """Start background cleanup thread."""
        def cleanup_worker():
            while not self._shutdown_event.wait(interval):
                try:
                    self._cleanup_expired()
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate cache key from data."""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        key_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (dict, list)):
                return len(json.dumps(value).encode('utf-8'))
            elif hasattr(value, '__sizeof__'):
                return value.__sizeof__()
            else:
                return len(str(value).encode('utf-8'))
        except Exception:
            return 1024  # Default estimate
    
    def _cleanup_expired(self) -> int:
        """Clean up expired entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self.metrics.expired_entries += 1
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def _evict_if_needed(self):
        """Evict entries if cache is full."""
        if len(self._cache) < self.max_size:
            return
        
        with self._lock:
            if self.strategy == CacheStrategy.LRU:
                # Remove oldest entry (OrderedDict maintains insertion order)
                if self._cache:
                    self._cache.popitem(last=False)
                    self.metrics.evictions += 1
            
            elif self.strategy == CacheStrategy.LFU:
                # Remove least frequently used
                if self._cache:
                    lfu_key = min(self._cache.keys(), 
                                 key=lambda k: self._cache[k].access_count)
                    del self._cache[lfu_key]
                    self.metrics.evictions += 1
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()
        
        with self._lock:
            self.metrics.total_requests += 1
            
            entry = self._cache.get(key)
            if entry is None:
                self.metrics.misses += 1
                self.metrics.update_hit_rate()
                return None
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self.metrics.misses += 1
                self.metrics.expired_entries += 1
                self.metrics.update_hit_rate()
                return None
            
            # Update access metadata
            entry.update_access()
            
            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                self._cache.move_to_end(key)
            
            self.metrics.hits += 1
            self.metrics.update_hit_rate()
            
            # Update response time
            response_time_ms = (time.time() - start_time) * 1000
            self.metrics.avg_response_time_ms = (
                (self.metrics.avg_response_time_ms * (self.metrics.total_requests - 1) + response_time_ms) 
                / self.metrics.total_requests
            )
            
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        size_bytes = self._estimate_size(value)
        
        with self._lock:
            # Check memory limit
            current_memory = sum(entry.size_bytes for entry in self._cache.values())
            if current_memory + size_bytes > self.max_memory_bytes:
                logger.warning(f"Cache memory limit approached: {current_memory + size_bytes} bytes")
                # Force cleanup
                self._cleanup_expired()
                self._evict_if_needed()
            
            # Evict if needed
            self._evict_if_needed()
            
            # Create entry
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            self._cache[key] = entry
            
            # Update memory usage
            self.metrics.memory_usage_bytes = sum(
                entry.size_bytes for entry in self._cache.values()
            )
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self.metrics = CacheMetrics()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "max_size": self.max_size,
                "memory_usage_mb": self.metrics.memory_usage_bytes / (1024 * 1024),
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
                "hit_rate": self.metrics.hit_rate,
                "hits": self.metrics.hits,
                "misses": self.metrics.misses,
                "evictions": self.metrics.evictions,
                "expired_entries": self.metrics.expired_entries,
                "avg_response_time_ms": self.metrics.avg_response_time_ms,
                "strategy": self.strategy.value
            }
    
    async def get_or_compute(self, 
                           key: str, 
                           compute_func: Callable, 
                           ttl: Optional[float] = None,
                           use_coalescing: bool = True) -> Any:
        """
        Get value from cache or compute if not present.
        Supports request coalescing for duplicate queries.
        """
        # Try cache first
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Compute value with optional coalescing
        if use_coalescing:
            value = await self.coalescer.coalesce_request(key, compute_func)
        else:
            value = await compute_func()
        
        # Cache the result
        self.set(key, value, ttl)
        return value
    
    def shutdown(self):
        """Shutdown cache and cleanup resources."""
        self._shutdown_event.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=5.0)
        logger.info("Performance cache shutdown completed")
    
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self.shutdown()
        except Exception:
            pass

class CacheManager:
    """Centralized cache manager for different cache types."""
    
    def __init__(self):
        self._caches: Dict[str, PerformanceCache] = {}
        self._lock = threading.Lock()
    
    def get_cache(self, 
                  name: str,
                  max_size: int = 1000,
                  default_ttl: float = 300.0,
                  strategy: CacheStrategy = CacheStrategy.LRU) -> PerformanceCache:
        """Get or create named cache."""
        with self._lock:
            if name not in self._caches:
                self._caches[name] = PerformanceCache(
                    max_size=max_size,
                    default_ttl=default_ttl,
                    strategy=strategy
                )
                logger.info(f"Created cache '{name}' with {max_size} max entries")
            
            return self._caches[name]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        with self._lock:
            return {
                name: cache.get_stats() 
                for name, cache in self._caches.items()
            }
    
    def clear_all(self):
        """Clear all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
    
    def shutdown_all(self):
        """Shutdown all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.shutdown()
            self._caches.clear()

# Global cache manager instance
cache_manager = CacheManager()

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    return cache_manager

# Pre-configured caches for common use cases
def get_rag_query_cache() -> PerformanceCache:
    """Get cache optimized for RAG queries."""
    return cache_manager.get_cache(
        name="rag_queries",
        max_size=500,
        default_ttl=300.0,  # 5 minutes
        strategy=CacheStrategy.LRU
    )

def get_document_cache() -> PerformanceCache:
    """Get cache for document metadata."""
    return cache_manager.get_cache(
        name="documents",
        max_size=1000,
        default_ttl=600.0,  # 10 minutes
        strategy=CacheStrategy.LRU
    )

def get_embedding_cache() -> PerformanceCache:
    """Get cache for embeddings."""
    return cache_manager.get_cache(
        name="embeddings",
        max_size=2000,
        default_ttl=1800.0,  # 30 minutes
        strategy=CacheStrategy.LRU
    )