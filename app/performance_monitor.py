"""
Authored by: Performance Engineer (chacha)
Date: 2025-08-05

Performance Monitoring System

Comprehensive performance monitoring with metrics collection, alerting,
and dashboard capabilities for the RAG system.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any, Callable, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import statistics
import weakref
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass 
class AlertRule:
    """Performance alert rule definition."""
    name: str
    metric_name: str
    threshold: float
    comparison: str = ">"  # >, <, >=, <=, ==, !=
    level: AlertLevel = AlertLevel.WARNING
    duration_seconds: float = 60.0  # Alert after threshold exceeded for this duration
    cooldown_seconds: float = 300.0  # Minimum time between alerts
    enabled: bool = True
    
    def evaluate(self, current_value: float, duration: float) -> bool:
        """Evaluate if alert should trigger."""
        if not self.enabled:
            return False
        
        if duration < self.duration_seconds:
            return False
        
        if self.comparison == ">":
            return current_value > self.threshold
        elif self.comparison == "<":
            return current_value < self.threshold
        elif self.comparison == ">=":
            return current_value >= self.threshold
        elif self.comparison == "<=":
            return current_value <= self.threshold
        elif self.comparison == "==":
            return current_value == self.threshold
        elif self.comparison == "!=":
            return current_value != self.threshold
        
        return False

@dataclass
class AlertEvent:
    """Alert event record."""
    rule_name: str
    metric_name: str
    level: AlertLevel
    value: float
    threshold: float
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None

class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: 'PerformanceMonitor', metric_name: str, labels: Dict[str, str] = None):
        self.monitor = monitor
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = (time.time() - self.start_time) * 1000  # Convert to milliseconds
            self.monitor.record_timer(self.metric_name, duration, self.labels)

class PerformanceMonitor:
    """
    Comprehensive performance monitoring system with metrics collection,
    alerting, and real-time dashboard capabilities.
    """
    
    def __init__(self, 
                 retention_seconds: int = 3600,  # 1 hour
                 max_points_per_metric: int = 1000,
                 alert_check_interval: float = 30.0):
        """
        Initialize performance monitor.
        
        Args:
            retention_seconds: How long to keep metric data
            max_points_per_metric: Maximum data points per metric
            alert_check_interval: How often to check alerts (seconds)
        """
        self.retention_seconds = retention_seconds
        self.max_points_per_metric = max_points_per_metric
        
        # Metrics storage
        self._metrics: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._metric_types: Dict[str, MetricType] = {}
        self._lock = threading.RLock()
        
        # Alerting system
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, AlertEvent] = {}
        self._alert_history: deque = deque(maxlen=1000)
        self._alert_callbacks: List[Callable[[AlertEvent], None]] = []
        
        # Alert monitoring thread
        self._alert_thread = None
        self._shutdown_event = threading.Event()
        self._start_alert_monitor(alert_check_interval)
        
        # Performance targets for the RAG system
        self._initialize_default_alerts()
        
        logger.info("Performance monitor initialized with alerting system")
    
    def _initialize_default_alerts(self):
        """Initialize default alert rules for RAG system performance targets."""
        default_alerts = [
            # Response time alerts
            AlertRule(
                name="slow_rag_queries",
                metric_name="rag_query_time",
                threshold=2000.0,  # 2 seconds
                comparison=">",
                level=AlertLevel.WARNING,
                duration_seconds=60.0
            ),
            AlertRule(
                name="very_slow_rag_queries", 
                metric_name="rag_query_time",
                threshold=5000.0,  # 5 seconds
                comparison=">",
                level=AlertLevel.ERROR,
                duration_seconds=30.0
            ),
            
            # Cache performance alerts
            AlertRule(
                name="low_cache_hit_rate",
                metric_name="cache_hit_rate",
                threshold=50.0,  # 50%
                comparison="<",
                level=AlertLevel.WARNING,
                duration_seconds=300.0  # 5 minutes
            ),
            
            # Memory usage alerts
            AlertRule(
                name="high_memory_usage",
                metric_name="memory_usage_mb",
                threshold=1500.0,  # 1.5GB
                comparison=">",
                level=AlertLevel.WARNING,
                duration_seconds=120.0
            ),
            
            # Error rate alerts
            AlertRule(
                name="high_error_rate",
                metric_name="error_rate",
                threshold=5.0,  # 5%
                comparison=">",
                level=AlertLevel.ERROR,
                duration_seconds=60.0
            ),
            
            # Connection pool alerts
            AlertRule(
                name="connection_pool_exhaustion",
                metric_name="pool_utilization",
                threshold=90.0,  # 90%
                comparison=">",
                level=AlertLevel.WARNING,
                duration_seconds=30.0
            )
        ]
        
        for alert in default_alerts:
            self.add_alert_rule(alert)
    
    def _start_alert_monitor(self, interval: float):
        """Start alert monitoring thread."""
        def alert_monitor():
            while not self._shutdown_event.wait(interval):
                try:
                    self._check_alerts()
                except Exception as e:
                    logger.error(f"Alert monitor error: {e}")
        
        self._alert_thread = threading.Thread(target=alert_monitor, daemon=True)
        self._alert_thread.start()
    
    def _cleanup_old_data(self):
        """Clean up old metric data points."""
        cutoff_time = time.time() - self.retention_seconds
        
        with self._lock:
            for metric_name, metric_data in self._metrics.items():
                for labels_key, points in metric_data.items():
                    # Remove old points
                    while points and points[0].timestamp < cutoff_time:
                        points.popleft()
                    
                    # Limit number of points
                    while len(points) > self.max_points_per_metric:
                        points.popleft()
    
    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record a counter metric (cumulative)."""
        self._record_metric(name, value, MetricType.COUNTER, labels)
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge metric (current value)."""
        self._record_metric(name, value, MetricType.GAUGE, labels)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric (distribution of values)."""
        self._record_metric(name, value, MetricType.HISTOGRAM, labels)
    
    def record_timer(self, name: str, duration_ms: float, labels: Dict[str, str] = None):
        """Record a timer metric (operation duration)."""
        self._record_metric(name, duration_ms, MetricType.TIMER, labels)
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, labels: Dict[str, str] = None):
        """Internal method to record metric data."""
        labels = labels or {}
        labels_key = json.dumps(labels, sort_keys=True)
        
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels
        )
        
        with self._lock:
            self._metric_types[name] = metric_type
            self._metrics[name][labels_key].append(point)
        
        # Cleanup old data periodically
        if hash(name) % 100 == 0:  # Do cleanup for ~1% of metrics
            self._cleanup_old_data()
    
    def timer(self, name: str, labels: Dict[str, str] = None) -> PerformanceTimer:
        """Create a context manager for timing operations."""
        return PerformanceTimer(self, name, labels)
    
    def get_metric_summary(self, name: str, labels: Dict[str, str] = None, 
                          duration_seconds: float = 300.0) -> Dict[str, Any]:
        """Get summary statistics for a metric over the specified duration."""
        labels_key = json.dumps(labels or {}, sort_keys=True)
        cutoff_time = time.time() - duration_seconds
        
        with self._lock:
            if name not in self._metrics:
                return {"error": f"Metric '{name}' not found"}
            
            if labels_key not in self._metrics[name]:
                return {"error": f"Labels {labels} not found for metric '{name}'"}
            
            points = self._metrics[name][labels_key]
            recent_points = [p for p in points if p.timestamp >= cutoff_time]
            
            if not recent_points:
                return {"error": "No recent data points"}
            
            values = [p.value for p in recent_points]
            metric_type = self._metric_types.get(name, MetricType.GAUGE)
            
            summary = {
                "metric_name": name,
                "metric_type": metric_type.value,
                "labels": labels or {},
                "duration_seconds": duration_seconds,
                "sample_count": len(values),
                "latest_value": values[-1],
                "timestamp": recent_points[-1].timestamp
            }
            
            if len(values) > 1:
                summary.update({
                    "min": min(values),
                    "max": max(values),
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "p95": self._percentile(values, 95),
                    "p99": self._percentile(values, 99)
                })
                
                # Rate calculation for counters
                if metric_type == MetricType.COUNTER and len(recent_points) > 1:
                    time_diff = recent_points[-1].timestamp - recent_points[0].timestamp
                    value_diff = recent_points[-1].value - recent_points[0].value
                    summary["rate_per_second"] = value_diff / max(time_diff, 1.0)
            
            return summary
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100.0) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        with self._lock:
            self._alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule."""
        with self._lock:
            self._alert_rules.pop(rule_name, None)
            # Resolve any active alerts for this rule
            if rule_name in self._active_alerts:
                alert = self._active_alerts[rule_name]
                alert.resolved = True
                alert.resolved_at = time.time()
                del self._active_alerts[rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    def add_alert_callback(self, callback: Callable[[AlertEvent], None]):
        """Add callback for alert events."""
        self._alert_callbacks.append(callback)
    
    def _check_alerts(self):
        """Check all alert rules against current metrics."""
        current_time = time.time()
        
        with self._lock:
            for rule_name, rule in self._alert_rules.items():
                try:
                    # Get recent metric summary
                    summary = self.get_metric_summary(rule.metric_name, duration_seconds=rule.duration_seconds)
                    
                    if "error" in summary:
                        continue
                    
                    current_value = summary.get("latest_value", 0.0)
                    duration_exceeded = summary.get("duration_seconds", 0.0)
                    
                    # Check if alert should trigger
                    should_alert = rule.evaluate(current_value, duration_exceeded)
                    
                    if should_alert and rule_name not in self._active_alerts:
                        # New alert
                        alert = AlertEvent(
                            rule_name=rule_name,
                            metric_name=rule.metric_name,
                            level=rule.level,
                            value=current_value,
                            threshold=rule.threshold,
                            message=f"{rule.metric_name} {rule.comparison} {rule.threshold} (current: {current_value:.2f})",
                            timestamp=current_time
                        )
                        
                        self._active_alerts[rule_name] = alert
                        self._alert_history.append(alert)
                        
                        # Notify callbacks
                        for callback in self._alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                logger.error(f"Alert callback error: {e}")
                        
                        logger.warning(f"ALERT TRIGGERED: {alert.message}")
                    
                    elif not should_alert and rule_name in self._active_alerts:
                        # Resolve alert
                        alert = self._active_alerts[rule_name]
                        alert.resolved = True
                        alert.resolved_at = current_time
                        del self._active_alerts[rule_name]
                        
                        logger.info(f"ALERT RESOLVED: {rule_name}")
                
                except Exception as e:
                    logger.error(f"Error checking alert rule {rule_name}: {e}")
    
    def get_dashboard_data(self, duration_seconds: float = 300.0) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        dashboard = {
            "timestamp": time.time(),
            "duration_seconds": duration_seconds,
            "metrics": {},
            "alerts": {
                "active_count": len(self._active_alerts),
                "active_alerts": [
                    {
                        "rule_name": alert.rule_name,
                        "level": alert.level.value,
                        "message": alert.message,
                        "duration": time.time() - alert.timestamp
                    }
                    for alert in self._active_alerts.values()
                ],
                "recent_history": [
                    {
                        "rule_name": alert.rule_name,
                        "level": alert.level.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp,
                        "resolved": alert.resolved
                    }
                    for alert in list(self._alert_history)[-10:]  # Last 10 alerts
                ]
            },
            "system_health": {
                "total_metrics": len(self._metric_types),
                "data_points": sum(
                    sum(len(points) for points in metric_data.values())
                    for metric_data in self._metrics.values()
                )
            }
        }
        
        # Get summaries for key metrics
        key_metrics = [
            "rag_query_time", "cache_hit_rate", "memory_usage_mb", 
            "error_rate", "pool_utilization", "embedding_time"
        ]
        
        for metric_name in key_metrics:
            try:
                summary = self.get_metric_summary(metric_name, duration_seconds=duration_seconds)
                if "error" not in summary:
                    dashboard["metrics"][metric_name] = summary
            except Exception as e:
                logger.debug(f"Could not get summary for {metric_name}: {e}")
        
        return dashboard
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "generation_time": datetime.now().isoformat(),
            "monitoring_duration": self.retention_seconds,
            "dashboard": self.get_dashboard_data(duration_seconds=3600),  # 1 hour
            "performance_targets": {
                "rag_query_time": {"target": "<2000ms", "critical": "<5000ms"},
                "cache_hit_rate": {"target": ">70%", "warning": "<50%"},
                "memory_usage": {"warning": ">1.5GB", "critical": ">2GB"},
                "error_rate": {"warning": ">1%", "critical": ">5%"},
                "pool_utilization": {"warning": ">80%", "critical": ">95%"}
            },
            "alert_summary": {
                "total_rules": len(self._alert_rules),
                "active_alerts": len(self._active_alerts),
                "alerts_in_last_hour": len([
                    a for a in self._alert_history 
                    if a.timestamp > time.time() - 3600
                ])
            }
        }
        
        return report
    
    def shutdown(self):
        """Shutdown performance monitor."""
        self._shutdown_event.set()
        if self._alert_thread and self._alert_thread.is_alive():
            self._alert_thread.join(timeout=5.0)
        logger.info("Performance monitor shutdown completed")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    return performance_monitor

# Convenience functions for common metrics
def record_rag_query_time(duration_ms: float, cache_hit: bool = False):
    """Record RAG query timing with cache hit information."""
    labels = {"cache_hit": str(cache_hit).lower()}
    performance_monitor.record_timer("rag_query_time", duration_ms, labels)

def record_cache_hit_rate(hit_rate: float, cache_name: str):
    """Record cache hit rate."""
    labels = {"cache_name": cache_name}
    performance_monitor.record_gauge("cache_hit_rate", hit_rate, labels)

def record_memory_usage(usage_mb: float, component: str = "system"):
    """Record memory usage."""
    labels = {"component": component}
    performance_monitor.record_gauge("memory_usage_mb", usage_mb, labels)

def record_error_rate(error_rate: float, component: str = "system"):
    """Record error rate percentage."""
    labels = {"component": component}
    performance_monitor.record_gauge("error_rate", error_rate, labels)

def record_pool_utilization(utilization_pct: float, pool_name: str):
    """Record connection pool utilization."""
    labels = {"pool_name": pool_name}
    performance_monitor.record_gauge("pool_utilization", utilization_pct, labels)