"""
Authored by: Performance Engineer (chacha)
Date: 2025-08-05

Connection Pool Manager

High-performance connection pooling for ChromaDB and Ollama services.
Provides connection reuse, health monitoring, and automatic failover.
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional, Any, Callable, AsyncContextManager
from dataclasses import dataclass, field
from enum import Enum
import weakref
from contextlib import asynccontextmanager
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """Connection state enumeration."""
    IDLE = "idle"
    IN_USE = "in_use"
    FAILED = "failed"
    CLOSED = "closed"

@dataclass
class ConnectionMetrics:
    """Connection pool metrics."""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    avg_wait_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    connection_errors: int = 0
    pool_exhaustion_count: int = 0

@dataclass
class PooledConnection:
    """Pooled connection wrapper."""
    connection_id: str
    connection: Any
    created_at: float
    last_used: float
    use_count: int = 0
    state: ConnectionState = ConnectionState.IDLE
    error_count: int = 0
    
    def mark_used(self):
        """Mark connection as used."""
        self.last_used = time.time()
        self.use_count += 1
        self.state = ConnectionState.IN_USE
    
    def mark_idle(self):
        """Mark connection as idle."""
        self.state = ConnectionState.IDLE
    
    def mark_failed(self):
        """Mark connection as failed."""
        self.error_count += 1
        self.state = ConnectionState.FAILED
    
    def is_expired(self, max_age: float) -> bool:
        """Check if connection is expired."""
        return time.time() - self.created_at > max_age

class ConnectionPool:
    """Generic connection pool implementation."""
    
    def __init__(self,
                 name: str,
                 connection_factory: Callable,
                 min_connections: int = 2,
                 max_connections: int = 10,
                 max_idle_time: float = 300.0,  # 5 minutes
                 max_connection_age: float = 3600.0,  # 1 hour
                 health_check_interval: float = 60.0,  # 1 minute
                 connection_timeout: float = 30.0):
        """
        Initialize connection pool.
        
        Args:
            name: Pool name for logging
            connection_factory: Function to create new connections
            min_connections: Minimum pool size
            max_connections: Maximum pool size
            max_idle_time: Max idle time before cleanup
            max_connection_age: Max connection age before renewal
            health_check_interval: Health check interval
            connection_timeout: Connection timeout
        """
        self.name = name
        self.connection_factory = connection_factory
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.max_connection_age = max_connection_age
        self.connection_timeout = connection_timeout
        
        # Pool storage
        self._pool: List[PooledConnection] = []
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        
        # Metrics
        self.metrics = ConnectionMetrics()
        
        # Health monitoring
        self._health_check_thread = None
        self._shutdown_event = threading.Event()
        
        # Initialize pool
        self._initialize_pool()
        self._start_health_monitor(health_check_interval)
        
        logger.info(f"Connection pool '{name}' initialized: "
                   f"min={min_connections}, max={max_connections}")
    
    def _initialize_pool(self):
        """Initialize the connection pool with minimum connections."""
        for i in range(self.min_connections):
            try:
                conn = self._create_connection()
                if conn:
                    self._pool.append(conn)
                    self.metrics.total_connections += 1
                    self.metrics.idle_connections += 1
            except Exception as e:
                logger.error(f"Failed to create initial connection for pool '{self.name}': {e}")
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new pooled connection."""
        try:
            connection = self.connection_factory()
            if connection is None:
                return None
            
            conn_id = f"{self.name}_{int(time.time() * 1000)}_{id(connection)}"
            pooled_conn = PooledConnection(
                connection_id=conn_id,
                connection=connection,
                created_at=time.time(),
                last_used=time.time()
            )
            
            logger.debug(f"Created new connection {conn_id} for pool '{self.name}'")
            return pooled_conn
            
        except Exception as e:
            logger.error(f"Failed to create connection for pool '{self.name}': {e}")
            self.metrics.connection_errors += 1
            return None
    
    def _start_health_monitor(self, interval: float):
        """Start health monitoring thread."""
        def health_monitor():
            while not self._shutdown_event.wait(interval):
                try:
                    self._cleanup_connections()
                    self._maintain_min_connections()
                except Exception as e:
                    logger.error(f"Health monitor error for pool '{self.name}': {e}")
        
        self._health_check_thread = threading.Thread(target=health_monitor, daemon=True)
        self._health_check_thread.start()
    
    def _cleanup_connections(self):
        """Clean up expired and failed connections."""
        current_time = time.time()
        
        with self._lock:
            to_remove = []
            
            for conn in self._pool:
                # Remove failed connections
                if conn.state == ConnectionState.FAILED:
                    to_remove.append(conn)
                    continue
                
                # Remove expired connections
                if conn.is_expired(self.max_connection_age):
                    to_remove.append(conn)
                    continue
                
                # Remove idle connections that exceed idle time
                if (conn.state == ConnectionState.IDLE and 
                    current_time - conn.last_used > self.max_idle_time and
                    len(self._pool) > self.min_connections):
                    to_remove.append(conn)
                    continue
            
            # Remove connections
            for conn in to_remove:
                self._pool.remove(conn)
                self.metrics.total_connections -= 1
                
                if conn.state == ConnectionState.IDLE:
                    self.metrics.idle_connections -= 1
                elif conn.state == ConnectionState.IN_USE:
                    self.metrics.active_connections -= 1
                elif conn.state == ConnectionState.FAILED:
                    self.metrics.failed_connections -= 1
                
                try:
                    self._close_connection(conn.connection)
                except Exception as e:
                    logger.warning(f"Error closing connection {conn.connection_id}: {e}")
            
            if to_remove:
                logger.debug(f"Cleaned up {len(to_remove)} connections from pool '{self.name}'")
    
    def _maintain_min_connections(self):
        """Maintain minimum number of connections."""
        with self._lock:
            idle_count = sum(1 for conn in self._pool if conn.state == ConnectionState.IDLE)
            
            if idle_count < self.min_connections:
                needed = self.min_connections - idle_count
                for _ in range(needed):
                    if len(self._pool) >= self.max_connections:
                        break
                    
                    conn = self._create_connection()
                    if conn:
                        self._pool.append(conn)
                        self.metrics.total_connections += 1
                        self.metrics.idle_connections += 1
    
    def _close_connection(self, connection: Any):
        """Close a connection (override in subclasses)."""
        if hasattr(connection, 'close'):
            connection.close()
    
    def get_connection(self, timeout: float = None) -> Optional[PooledConnection]:
        """Get a connection from the pool."""
        if timeout is None:
            timeout = self.connection_timeout
        
        start_time = time.time()
        
        with self._condition:
            # Try to find an idle connection
            for conn in self._pool:
                if conn.state == ConnectionState.IDLE:
                    conn.mark_used()
                    self.metrics.idle_connections -= 1
                    self.metrics.active_connections += 1
                    self.metrics.total_requests += 1
                    
                    # Update wait time
                    wait_time_ms = (time.time() - start_time) * 1000
                    self.metrics.avg_wait_time_ms = (
                        (self.metrics.avg_wait_time_ms * (self.metrics.total_requests - 1) + wait_time_ms)
                        / self.metrics.total_requests
                    )
                    
                    return conn
            
            # No idle connections, try to create new one
            if len(self._pool) < self.max_connections:
                conn = self._create_connection()
                if conn:
                    conn.mark_used()
                    self._pool.append(conn)
                    self.metrics.total_connections += 1
                    self.metrics.active_connections += 1
                    self.metrics.total_requests += 1
                    return conn
            
            # Pool exhausted, wait for connection
            self.metrics.pool_exhaustion_count += 1
            logger.warning(f"Connection pool '{self.name}' exhausted, waiting...")
            
            if self._condition.wait(timeout):
                # Try again after wait
                return self.get_connection(timeout - (time.time() - start_time))
            else:
                logger.error(f"Timeout waiting for connection from pool '{self.name}'")
                return None
    
    def return_connection(self, conn: PooledConnection, error_occurred: bool = False):
        """Return a connection to the pool."""
        with self._condition:
            if error_occurred:
                conn.mark_failed()
                self.metrics.active_connections -= 1
                self.metrics.failed_connections += 1
            else:
                conn.mark_idle()
                self.metrics.active_connections -= 1
                self.metrics.idle_connections += 1
            
            # Notify waiting threads
            self._condition.notify()
    
    @asynccontextmanager
    async def acquire_connection(self):
        """Async context manager for connection acquisition."""
        conn = None
        try:
            # Get connection (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            conn = await loop.run_in_executor(None, self.get_connection)
            
            if conn is None:
                raise Exception(f"Failed to acquire connection from pool '{self.name}'")
            
            yield conn.connection
            
        except Exception as e:
            if conn:
                self.return_connection(conn, error_occurred=True)
            raise
        else:
            if conn:
                self.return_connection(conn, error_occurred=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_name": self.name,
                "total_connections": self.metrics.total_connections,
                "active_connections": self.metrics.active_connections,
                "idle_connections": self.metrics.idle_connections,
                "failed_connections": self.metrics.failed_connections,
                "max_connections": self.max_connections,
                "min_connections": self.min_connections,
                "pool_utilization": self.metrics.active_connections / max(self.max_connections, 1) * 100,
                "total_requests": self.metrics.total_requests,
                "avg_wait_time_ms": self.metrics.avg_wait_time_ms,
                "connection_errors": self.metrics.connection_errors,
                "pool_exhaustion_count": self.metrics.pool_exhaustion_count
            }
    
    def shutdown(self):
        """Shutdown the connection pool."""
        self._shutdown_event.set()
        
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=5.0)
        
        with self._lock:
            for conn in self._pool:
                try:
                    self._close_connection(conn.connection)
                except Exception:
                    pass
            
            self._pool.clear()
            self.metrics = ConnectionMetrics()
        
        logger.info(f"Connection pool '{self.name}' shutdown completed")

class OllamaConnectionPool(ConnectionPool):
    """Specialized connection pool for Ollama HTTP clients."""
    
    def __init__(self, base_url: str, **kwargs):
        self.base_url = base_url
        
        def create_ollama_session():
            session = requests.Session()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=10
            )
            
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Set timeouts
            session.timeout = (5.0, 30.0)  # (connect, read)
            
            return session
        
        super().__init__(
            name="ollama_http",
            connection_factory=create_ollama_session,
            **kwargs
        )
    
    def _close_connection(self, connection):
        """Close HTTP session."""
        if hasattr(connection, 'close'):
            connection.close()

class ChromaDBConnectionPool(ConnectionPool):
    """Specialized connection pool for ChromaDB clients."""
    
    def __init__(self, chroma_path: str, **kwargs):
        self.chroma_path = chroma_path
        
        def create_chroma_client():
            return chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(anonymized_telemetry=False)
            )
        
        super().__init__(
            name="chromadb",
            connection_factory=create_chroma_client,
            **kwargs
        )

class ConnectionPoolManager:
    """Centralized connection pool manager."""
    
    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._lock = threading.Lock()
    
    def create_ollama_pool(self, 
                          name: str = "default_ollama",
                          base_url: str = "http://localhost:11434",
                          min_connections: int = 2,
                          max_connections: int = 8) -> OllamaConnectionPool:
        """Create Ollama connection pool."""
        with self._lock:
            if name in self._pools:
                return self._pools[name]
            
            pool = OllamaConnectionPool(
                base_url=base_url,
                min_connections=min_connections,
                max_connections=max_connections
            )
            
            self._pools[name] = pool
            logger.info(f"Created Ollama connection pool '{name}' for {base_url}")
            return pool
    
    def create_chromadb_pool(self,
                           name: str = "default_chromadb", 
                           chroma_path: str = "./data/chroma_db",
                           min_connections: int = 1,
                           max_connections: int = 4) -> ChromaDBConnectionPool:
        """Create ChromaDB connection pool."""
        with self._lock:
            if name in self._pools:
                return self._pools[name]
            
            pool = ChromaDBConnectionPool(
                chroma_path=chroma_path,
                min_connections=min_connections,
                max_connections=max_connections
            )
            
            self._pools[name] = pool
            logger.info(f"Created ChromaDB connection pool '{name}' for {chroma_path}")
            return pool
    
    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get connection pool by name."""
        with self._lock:
            return self._pools.get(name)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all pools."""
        with self._lock:
            return {
                name: pool.get_stats()
                for name, pool in self._pools.items()
            }
    
    def shutdown_all(self):
        """Shutdown all connection pools."""
        with self._lock:
            for pool in self._pools.values():
                pool.shutdown()
            self._pools.clear()

# Global connection pool manager
pool_manager = ConnectionPoolManager()

def get_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager."""
    return pool_manager