"""
System health monitoring and alerting for RAG application.
Monitors component health, performance metrics, and system resources.
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Component health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """System component types."""
    FASTAPI = "fastapi"
    REFLEX = "reflex"
    CHROMADB = "chromadb"
    OLLAMA = "ollama"
    EMBEDDINGS = "embeddings"
    FILE_PROCESSOR = "file_processor"
    SYSTEM = "system"


@dataclass
class HealthCheck:
    """Health check result for a component."""
    component: ComponentType
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "component": self.component.value,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "response_time_ms": self.response_time_ms
        }


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_available_gb: float
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_percent": round(self.memory_percent, 2),
            "memory_used_mb": round(self.memory_used_mb, 2),
            "memory_available_mb": round(self.memory_available_mb, 2),
            "disk_percent": round(self.disk_percent, 2),
            "disk_used_gb": round(self.disk_used_gb, 2),
            "disk_available_gb": round(self.disk_available_gb, 2),
            "active_connections": self.active_connections,
            "timestamp": self.timestamp.isoformat()
        }


class HealthMonitor:
    """System health monitoring and alerting."""
    
    def __init__(self):
        self.health_checks: Dict[ComponentType, HealthCheck] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 100
        self.alert_callbacks: Dict[HealthStatus, List[Callable]] = {
            HealthStatus.UNHEALTHY: [],
            HealthStatus.DEGRADED: []
        }
        self.check_interval = 30  # seconds
        self.is_monitoring = False
        self._monitoring_task = None
        
        # Thresholds
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0
        self.response_time_threshold_ms = 5000
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            logger.warning("Health monitoring already running")
            return
        
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Perform health checks
                await self.check_all_components()
                
                # Collect system metrics
                metrics = self.collect_system_metrics()
                self._add_metrics_to_history(metrics)
                
                # Check for alerts
                self._check_alerts()
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_all_components(self) -> Dict[ComponentType, HealthCheck]:
        """Check health of all components."""
        tasks = [
            self.check_fastapi(),
            self.check_chromadb(),
            self.check_ollama(),
            self.check_embeddings(),
            self.check_file_processor(),
            self.check_system_health()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, HealthCheck):
                self.health_checks[result.component] = result
            elif isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
        
        return self.health_checks
    
    async def check_fastapi(self) -> HealthCheck:
        """Check FastAPI backend health."""
        import aiohttp
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return HealthCheck(
                            component=ComponentType.FASTAPI,
                            status=HealthStatus.HEALTHY,
                            message="FastAPI backend is healthy",
                            details=data,
                            response_time_ms=response_time
                        )
                    else:
                        return HealthCheck(
                            component=ComponentType.FASTAPI,
                            status=HealthStatus.UNHEALTHY,
                            message=f"FastAPI returned status {response.status}",
                            response_time_ms=response_time
                        )
                        
        except Exception as e:
            return HealthCheck(
                component=ComponentType.FASTAPI,
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to connect to FastAPI: {str(e)}"
            )
    
    async def check_chromadb(self) -> HealthCheck:
        """Check ChromaDB health."""
        try:
            from rag_backend import get_rag_system
            rag = get_rag_system()
            
            start_time = time.time()
            doc_count = rag.collection.count()
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                component=ComponentType.CHROMADB,
                status=HealthStatus.HEALTHY,
                message="ChromaDB is operational",
                details={"document_count": doc_count},
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthCheck(
                component=ComponentType.CHROMADB,
                status=HealthStatus.UNHEALTHY,
                message=f"ChromaDB error: {str(e)}"
            )
    
    async def check_ollama(self) -> HealthCheck:
        """Check Ollama LLM service health."""
        try:
            from rag_backend import get_rag_system
            rag = get_rag_system()
            
            start_time = time.time()
            is_healthy = rag.llm_client.health_check()
            response_time = (time.time() - start_time) * 1000
            
            if is_healthy:
                return HealthCheck(
                    component=ComponentType.OLLAMA,
                    status=HealthStatus.HEALTHY,
                    message="Ollama service is running",
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    component=ComponentType.OLLAMA,
                    status=HealthStatus.UNHEALTHY,
                    message="Ollama service is not responding"
                )
                
        except Exception as e:
            return HealthCheck(
                component=ComponentType.OLLAMA,
                status=HealthStatus.DEGRADED,
                message=f"Ollama check failed: {str(e)}",
                details={"note": "System can operate without Ollama"}
            )
    
    async def check_embeddings(self) -> HealthCheck:
        """Check embedding model health."""
        try:
            from rag_backend import get_rag_system
            rag = get_rag_system()
            
            start_time = time.time()
            test_embedding = rag.encoder.encode("test").tolist()
            response_time = (time.time() - start_time) * 1000
            
            if len(test_embedding) == 384:  # Expected dimension
                return HealthCheck(
                    component=ComponentType.EMBEDDINGS,
                    status=HealthStatus.HEALTHY,
                    message="Embedding model is operational",
                    details={"embedding_dim": len(test_embedding)},
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    component=ComponentType.EMBEDDINGS,
                    status=HealthStatus.DEGRADED,
                    message=f"Unexpected embedding dimension: {len(test_embedding)}"
                )
                
        except Exception as e:
            return HealthCheck(
                component=ComponentType.EMBEDDINGS,
                status=HealthStatus.UNHEALTHY,
                message=f"Embedding model error: {str(e)}"
            )
    
    async def check_file_processor(self) -> HealthCheck:
        """Check file processing capability."""
        try:
            from document_processing_tracker import processing_tracker
            
            queue_status = processing_tracker.get_queue_status()
            
            # Check for stuck tasks
            processing_tasks = processing_tracker.get_tasks_by_status(
                processing_tracker.ProcessingStatus.PROCESSING
            )
            
            stuck_tasks = []
            for task in processing_tasks:
                if task.started_at:
                    processing_time = (datetime.now() - task.started_at).seconds
                    if processing_time > 300:  # 5 minutes
                        stuck_tasks.append(task.doc_id)
            
            if stuck_tasks:
                return HealthCheck(
                    component=ComponentType.FILE_PROCESSOR,
                    status=HealthStatus.DEGRADED,
                    message=f"{len(stuck_tasks)} tasks appear stuck",
                    details={
                        "queue_status": queue_status,
                        "stuck_tasks": stuck_tasks
                    }
                )
            else:
                return HealthCheck(
                    component=ComponentType.FILE_PROCESSOR,
                    status=HealthStatus.HEALTHY,
                    message="File processor is operational",
                    details={"queue_status": queue_status}
                )
                
        except Exception as e:
            return HealthCheck(
                component=ComponentType.FILE_PROCESSOR,
                status=HealthStatus.UNKNOWN,
                message=f"Could not check file processor: {str(e)}"
            )
    
    async def check_system_health(self) -> HealthCheck:
        """Check overall system health."""
        metrics = self.collect_system_metrics()
        
        issues = []
        if metrics.cpu_percent > self.cpu_threshold:
            issues.append(f"High CPU usage: {metrics.cpu_percent}%")
        if metrics.memory_percent > self.memory_threshold:
            issues.append(f"High memory usage: {metrics.memory_percent}%")
        if metrics.disk_percent > self.disk_threshold:
            issues.append(f"Low disk space: {metrics.disk_percent}% used")
        
        if issues:
            return HealthCheck(
                component=ComponentType.SYSTEM,
                status=HealthStatus.DEGRADED,
                message="; ".join(issues),
                details=metrics.to_dict()
            )
        else:
            return HealthCheck(
                component=ComponentType.SYSTEM,
                status=HealthStatus.HEALTHY,
                message="System resources are within normal parameters",
                details=metrics.to_dict()
            )
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_available_gb = disk.free / (1024 * 1024 * 1024)
        
        # Network connections (approximate active connections)
        connections = len(psutil.net_connections())
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            disk_percent=disk_percent,
            disk_used_gb=disk_used_gb,
            disk_available_gb=disk_available_gb,
            active_connections=connections
        )
    
    def _add_metrics_to_history(self, metrics: SystemMetrics):
        """Add metrics to history, maintaining size limit."""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
    
    def _check_alerts(self):
        """Check for conditions that require alerts."""
        for component, check in self.health_checks.items():
            if check.status == HealthStatus.UNHEALTHY:
                self._trigger_alerts(HealthStatus.UNHEALTHY, check)
            elif check.status == HealthStatus.DEGRADED:
                self._trigger_alerts(HealthStatus.DEGRADED, check)
    
    def _trigger_alerts(self, status: HealthStatus, check: HealthCheck):
        """Trigger registered alert callbacks."""
        callbacks = self.alert_callbacks.get(status, [])
        for callback in callbacks:
            try:
                callback(check)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def register_alert_callback(self, status: HealthStatus, callback: Callable):
        """Register a callback for health alerts."""
        self.alert_callbacks[status].append(callback)
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        total_components = len(self.health_checks)
        healthy = sum(1 for check in self.health_checks.values() 
                     if check.status == HealthStatus.HEALTHY)
        degraded = sum(1 for check in self.health_checks.values() 
                      if check.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for check in self.health_checks.values() 
                       if check.status == HealthStatus.UNHEALTHY)
        
        # Overall status
        if unhealthy > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_status = HealthStatus.DEGRADED
        elif healthy == total_components:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        # Get latest metrics
        latest_metrics = self.metrics_history[-1].to_dict() if self.metrics_history else None
        
        return {
            "overall_status": overall_status.value,
            "components": {
                "total": total_components,
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy
            },
            "checks": {
                component.value: check.to_dict() 
                for component, check in self.health_checks.items()
            },
            "latest_metrics": latest_metrics,
            "last_check": max(
                (check.checked_at for check in self.health_checks.values()),
                default=datetime.now()
            ).isoformat()
        }
    
    def get_metrics_history(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """Get metrics history for the specified time period."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        return [
            metric.to_dict() 
            for metric in self.metrics_history
            if metric.timestamp >= cutoff_time
        ]


# Global health monitor instance
health_monitor = HealthMonitor()