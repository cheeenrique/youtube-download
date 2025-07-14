import psutil
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import threading
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    name: str
    value: float
    type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class Alert:
    id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    source: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class HealthCheck:
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    timestamp: datetime
    response_time_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


class MonitoringService:
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Alert] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.metric_collectors: List[Callable[[], List[Metric]]] = []
        self.health_checkers: List[Callable[[], HealthCheck]] = []
        self.monitoring_enabled = True
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        # Setup default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default alert thresholds"""
        self.alert_thresholds = {
            "cpu_usage": {
                "warning": 70.0,
                "error": 85.0,
                "critical": 95.0
            },
            "memory_usage": {
                "warning": 80.0,
                "error": 90.0,
                "critical": 95.0
            },
            "disk_usage": {
                "warning": 80.0,
                "error": 90.0,
                "critical": 95.0
            },
            "response_time": {
                "warning": 1000.0,  # ms
                "error": 3000.0,
                "critical": 5000.0
            },
            "error_rate": {
                "warning": 5.0,  # percentage
                "error": 10.0,
                "critical": 20.0
            }
        }
    
    def add_metric(self, metric: Metric) -> None:
        """Add a metric to the monitoring service"""
        if not self.monitoring_enabled:
            return
        
        self.metrics[metric.name].append(metric)
        
        # Check for alerts
        self._check_alerts(metric)
    
    def _check_alerts(self, metric: Metric) -> None:
        """Check if metric triggers any alerts"""
        if metric.name not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[metric.name]
        
        for severity_name, threshold in thresholds.items():
            severity = AlertSeverity(severity_name.upper())
            
            # Check if threshold is exceeded
            if metric.value >= threshold:
                # Check if alert already exists and is not resolved
                existing_alert = next(
                    (alert for alert in self.alerts 
                     if alert.name == f"{metric.name}_{severity_name}" 
                     and not alert.resolved),
                    None
                )
                
                if not existing_alert:
                    # Create new alert
                    alert = Alert(
                        id=f"{metric.name}_{severity_name}_{int(time.time())}",
                        name=f"{metric.name}_{severity_name}",
                        severity=severity,
                        message=f"{metric.name} exceeded {severity_name} threshold: {metric.value} >= {threshold}",
                        timestamp=datetime.utcnow(),
                        source="monitoring_service",
                        metric_name=metric.name,
                        metric_value=metric.value,
                        threshold=threshold
                    )
                    
                    self.alerts.append(alert)
                    self._trigger_alert_handlers(alert)
                    logger.warning(f"Alert triggered: {alert.message}")
            
            else:
                # Resolve existing alert if metric is back to normal
                existing_alert = next(
                    (alert for alert in self.alerts 
                     if alert.name == f"{metric.name}_{severity_name}" 
                     and not alert.resolved),
                    None
                )
                
                if existing_alert:
                    existing_alert.resolved = True
                    existing_alert.resolved_at = datetime.utcnow()
                    logger.info(f"Alert resolved: {existing_alert.name}")
    
    def _trigger_alert_handlers(self, alert: Alert) -> None:
        """Trigger all registered alert handlers"""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {str(e)}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def add_metric_collector(self, collector: Callable[[], List[Metric]]) -> None:
        """Add a metric collector function"""
        self.metric_collectors.append(collector)
    
    def add_health_checker(self, checker: Callable[[], HealthCheck]) -> None:
        """Add a health checker function"""
        self.health_checkers.append(checker)
    
    def collect_system_metrics(self) -> List[Metric]:
        """Collect basic system metrics"""
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(Metric(
                name="cpu_usage",
                value=cpu_percent,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="CPU usage percentage"
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            metrics.append(Metric(
                name="memory_usage",
                value=memory_percent,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Memory usage percentage"
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(Metric(
                name="disk_usage",
                value=disk_percent,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Disk usage percentage"
            ))
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics.append(Metric(
                name="network_bytes_sent",
                value=network.bytes_sent,
                type=MetricType.COUNTER,
                timestamp=timestamp,
                description="Network bytes sent"
            ))
            
            metrics.append(Metric(
                name="network_bytes_recv",
                value=network.bytes_recv,
                type=MetricType.COUNTER,
                timestamp=timestamp,
                description="Network bytes received"
            ))
            
            # Process count
            process_count = len(psutil.pids())
            metrics.append(Metric(
                name="process_count",
                value=process_count,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Number of running processes"
            ))
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
        
        return metrics
    
    def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        health_results = {}
        
        for checker in self.health_checkers:
            try:
                start_time = time.time()
                health_check = checker()
                end_time = time.time()
                
                # Add response time if not provided
                if health_check.response_time_ms is None:
                    health_check.response_time_ms = (end_time - start_time) * 1000
                
                health_results[health_check.name] = health_check
                self.health_checks[health_check.name] = health_check
                
            except Exception as e:
                logger.error(f"Error in health check {checker.__name__}: {str(e)}")
                health_check = HealthCheck(
                    name=checker.__name__,
                    status="unhealthy",
                    message=f"Health check failed: {str(e)}",
                    timestamp=datetime.utcnow(),
                    response_time_ms=None
                )
                health_results[health_check.name] = health_check
        
        return health_results
    
    def get_metrics(self, metric_name: Optional[str] = None, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[Metric]:
        """Get metrics with optional filtering"""
        if metric_name:
            metrics = list(self.metrics.get(metric_name, []))
        else:
            metrics = []
            for metric_list in self.metrics.values():
                metrics.extend(metric_list)
        
        # Filter by time range
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        return sorted(metrics, key=lambda x: x.timestamp)
    
    def get_metric_stats(self, metric_name: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get statistics for a specific metric"""
        metrics = self.get_metrics(metric_name, start_time, end_time)
        
        if not metrics:
            return {
                "metric_name": metric_name,
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "median": None,
                "std_dev": None
            }
        
        values = [m.value for m in metrics]
        
        return {
            "metric_name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "latest_value": values[-1],
            "latest_timestamp": metrics[-1].timestamp
        }
    
    def get_alerts(self, severity: Optional[AlertSeverity] = None,
                  resolved: Optional[bool] = None,
                  start_time: Optional[datetime] = None) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        if start_time:
            alerts = [a for a in alerts if a.timestamp >= start_time]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        health_checks = list(self.health_checks.values())
        
        if not health_checks:
            return {
                "status": "unknown",
                "message": "No health checks available",
                "checks_count": 0,
                "healthy_count": 0,
                "unhealthy_count": 0,
                "degraded_count": 0
            }
        
        healthy_count = sum(1 for h in health_checks if h.status == "healthy")
        unhealthy_count = sum(1 for h in health_checks if h.status == "unhealthy")
        degraded_count = sum(1 for h in health_checks if h.status == "degraded")
        
        # Determine overall status
        if unhealthy_count > 0:
            overall_status = "unhealthy"
            message = f"{unhealthy_count} health checks failed"
        elif degraded_count > 0:
            overall_status = "degraded"
            message = f"{degraded_count} health checks degraded"
        else:
            overall_status = "healthy"
            message = "All health checks passing"
        
        return {
            "status": overall_status,
            "message": message,
            "checks_count": len(health_checks),
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "degraded_count": degraded_count,
            "checks": [
                {
                    "name": h.name,
                    "status": h.status,
                    "message": h.message,
                    "response_time_ms": h.response_time_ms
                }
                for h in health_checks
            ]
        }
    
    def set_alert_threshold(self, metric_name: str, severity: str, threshold: float) -> None:
        """Set alert threshold for a metric"""
        if metric_name not in self.alert_thresholds:
            self.alert_thresholds[metric_name] = {}
        
        self.alert_thresholds[metric_name][severity] = threshold
    
    def start_monitoring(self, interval_seconds: int = 60) -> None:
        """Start continuous monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring is already running")
            return
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Started monitoring with {interval_seconds}s interval")
    
    def stop_monitoring_service(self) -> None:
        """Stop continuous monitoring"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped monitoring service")
    
    def _monitoring_loop(self, interval_seconds: int) -> None:
        """Main monitoring loop"""
        while not self.stop_monitoring:
            try:
                # Collect system metrics
                system_metrics = self.collect_system_metrics()
                for metric in system_metrics:
                    self.add_metric(metric)
                
                # Collect custom metrics
                for collector in self.metric_collectors:
                    try:
                        custom_metrics = collector()
                        for metric in custom_metrics:
                            self.add_metric(metric)
                    except Exception as e:
                        logger.error(f"Error in metric collector: {str(e)}")
                
                # Run health checks
                self.run_health_checks()
                
                # Sleep for interval
                time.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(interval_seconds)
    
    def cleanup_old_data(self, days_to_keep: int = 7) -> int:
        """Clean up old metrics and alerts"""
        cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean up old metrics
        metrics_cleaned = 0
        for metric_name, metric_list in self.metrics.items():
            original_count = len(metric_list)
            self.metrics[metric_name] = deque(
                [m for m in metric_list if m.timestamp > cutoff_time],
                maxlen=1000
            )
            metrics_cleaned += original_count - len(self.metrics[metric_name])
        
        # Clean up old alerts
        original_alert_count = len(self.alerts)
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp > cutoff_time
        ]
        alerts_cleaned = original_alert_count - len(self.alerts)
        
        logger.info(f"Cleaned up {metrics_cleaned} old metrics and {alerts_cleaned} old alerts")
        return metrics_cleaned + alerts_cleaned
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        # Get recent metrics (last hour)
        recent_metrics = self.get_metrics(
            start_time=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Get recent alerts (last 24 hours)
        recent_alerts = self.get_alerts(
            start_time=datetime.utcnow() - timedelta(days=1)
        )
        
        # Get health status
        health_status = self.get_health_status()
        
        # Calculate active alerts by severity
        active_alerts = self.get_alerts(resolved=False)
        alerts_by_severity = defaultdict(int)
        for alert in active_alerts:
            alerts_by_severity[alert.severity.value] += 1
        
        return {
            "metrics_count": len(recent_metrics),
            "active_alerts_count": len(active_alerts),
            "alerts_by_severity": dict(alerts_by_severity),
            "health_status": health_status,
            "monitoring_enabled": self.monitoring_enabled,
            "timestamp": datetime.utcnow().isoformat()
        } 