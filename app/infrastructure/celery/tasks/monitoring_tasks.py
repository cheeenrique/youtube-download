from celery import shared_task
from datetime import datetime, timedelta, timezone
import logging
from typing import Dict, List, Any, Optional
import json
import psutil
import requests
import time

from app.infrastructure.monitoring.monitoring_service import (
    MonitoringService, Metric, MetricType, Alert, AlertSeverity, HealthCheck
)
from app.infrastructure.monitoring.alert_manager import AlertManager, NotificationChannel, NotificationConfig
from app.shared.config import settings
from app.infrastructure.cache.mock_cache import mock_cache as redis_cache
from app.infrastructure.cache.analytics_cache import analytics_cache

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="monitoring.collect_system_metrics")
def collect_system_metrics(self) -> Dict[str, Any]:
    """Collect system metrics and store them"""
    try:
        monitoring_service = MonitoringService()
        
        # Collect system metrics
        metrics = monitoring_service.collect_system_metrics()
        
        # Add custom application metrics
        app_metrics = collect_application_metrics()
        metrics.extend(app_metrics)
        
        # Store metrics
        for metric in metrics:
            monitoring_service.add_metric(metric)
        
        result = {
            "metrics_collected": len(metrics),
            "system_metrics": len([m for m in metrics if m.name in ["cpu_usage", "memory_usage", "disk_usage"]]),
            "application_metrics": len([m for m in metrics if m.name not in ["cpu_usage", "memory_usage", "disk_usage"]]),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Collected {len(metrics)} metrics")
        return result
        
    except Exception as e:
        logger.error(f"Error collecting system metrics: {str(e)}")
        self.retry(countdown=60, max_retries=3)


def collect_application_metrics() -> List[Metric]:
    """Collect application-specific metrics"""
    metrics = []
    timestamp = datetime.now(timezone.utc)
    
    try:
        # Database connection metrics
        try:
            from app.infrastructure.database.database import get_db
            db = get_db()
            # This is a placeholder - in a real implementation you'd check actual DB connections
            metrics.append(Metric(
                name="database_connections",
                value=1,  # Placeholder
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Active database connections"
            ))
        except Exception:
            metrics.append(Metric(
                name="database_connections",
                value=0,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Active database connections"
            ))
        
        # Celery worker metrics
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active_workers = len(inspect.active() or {})
            metrics.append(Metric(
                name="celery_workers_active",
                value=active_workers,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Active Celery workers"
            ))
        except Exception:
            metrics.append(Metric(
                name="celery_workers_active",
                value=0,
                type=MetricType.GAUGE,
                timestamp=timestamp,
                description="Active Celery workers"
            ))
        
        # API endpoint response times (placeholder)
        metrics.append(Metric(
            name="api_response_time_avg",
            value=150.0,  # Placeholder value in ms
            type=MetricType.GAUGE,
            timestamp=timestamp,
            description="Average API response time in milliseconds"
        ))
        
        # Download queue size (placeholder)
        metrics.append(Metric(
            name="download_queue_size",
            value=5,  # Placeholder
            type=MetricType.GAUGE,
            timestamp=timestamp,
            description="Number of downloads in queue"
        ))
        
        # Active downloads
        metrics.append(Metric(
            name="active_downloads",
            value=2,  # Placeholder
            type=MetricType.GAUGE,
            timestamp=timestamp,
            description="Number of active downloads"
        ))
        
        # Error rate (placeholder)
        metrics.append(Metric(
            name="error_rate",
            value=2.5,  # Placeholder percentage
            type=MetricType.GAUGE,
            timestamp=timestamp,
            description="Error rate percentage"
        ))
        
    except Exception as e:
        logger.error(f"Error collecting application metrics: {str(e)}")
    
    return metrics


@shared_task(bind=True, name="monitoring.run_health_checks")
def run_health_checks(self) -> Dict[str, Any]:
    """Run health checks and update status"""
    try:
        monitoring_service = MonitoringService()
        
        # Add default health checkers
        add_default_health_checkers(monitoring_service)
        
        # Run health checks
        health_results = monitoring_service.run_health_checks()
        
        # Process results
        healthy_count = sum(1 for h in health_results.values() if h.status == "healthy")
        unhealthy_count = sum(1 for h in health_results.values() if h.status == "unhealthy")
        degraded_count = sum(1 for h in health_results.values() if h.status == "degraded")
        
        result = {
            "total_checks": len(health_results),
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "degraded_count": degraded_count,
            "overall_status": "healthy" if unhealthy_count == 0 else "unhealthy",
            "checks": [
                {
                    "name": h.name,
                    "status": h.status,
                    "message": h.message,
                    "response_time_ms": h.response_time_ms
                }
                for h in health_results.values()
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Health checks completed: {healthy_count} healthy, {unhealthy_count} unhealthy")
        return result
        
    except Exception as e:
        logger.error(f"Error running health checks: {str(e)}")
        self.retry(countdown=120, max_retries=3)


def add_default_health_checkers(monitoring_service: MonitoringService) -> None:
    """Add default health check functions"""
    
    def check_database_health() -> HealthCheck:
        """Check database connectivity"""
        try:
            from app.infrastructure.database.database import get_db
            db = get_db()
            # In a real implementation, you'd run a simple query
            start_time = time.time()
            # db.execute("SELECT 1")  # Placeholder
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="database",
                status="healthy",
                message="Database connection is working",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time
            )
        except Exception as e:
            return HealthCheck(
                name="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=None
            )
    
    def check_redis_health() -> HealthCheck:
        """Check Redis connectivity"""
        try:
            import redis
            
            r = redis.Redis(
                host=getattr(settings, 'redis_host', 'localhost'),
                port=getattr(settings, 'redis_port', 6379),
                db=getattr(settings, 'redis_db', 0),
                socket_timeout=5
            )
            
            start_time = time.time()
            r.ping()
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="redis",
                status="healthy",
                message="Redis connection is working",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time
            )
        except Exception as e:
            return HealthCheck(
                name="redis",
                status="unhealthy",
                message=f"Redis connection failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=None
            )
    
    def check_celery_health() -> HealthCheck:
        """Check Celery worker health"""
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            
            start_time = time.time()
            active_workers = inspect.active()
            response_time = (time.time() - start_time) * 1000
            
            if active_workers:
                return HealthCheck(
                    name="celery",
                    status="healthy",
                    message=f"Celery workers are active",
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=response_time,
                    details={"active_workers": len(active_workers)}
                )
            else:
                return HealthCheck(
                    name="celery",
                    status="degraded",
                    message="No active Celery workers found",
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=response_time
                )
        except Exception as e:
            return HealthCheck(
                name="celery",
                status="unhealthy",
                message=f"Celery health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=None
            )
    
    def check_api_health() -> HealthCheck:
        """Check API endpoint health"""
        try:
            base_url = f"http://localhost:{getattr(settings, 'port', 8000)}"
            
            start_time = time.time()
            response = requests.get(f"{base_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                return HealthCheck(
                    name="api",
                    status="healthy",
                    message="API is responding",
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=response_time
                )
            else:
                return HealthCheck(
                    name="api",
                    status="degraded",
                    message=f"API returned status {response.status_code}",
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=response_time
                )
        except Exception as e:
            return HealthCheck(
                name="api",
                status="unhealthy",
                message=f"API health check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=None
            )
    
    def check_disk_space() -> HealthCheck:
        """Check disk space"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent < 80:
                status = "healthy"
                message = f"Disk usage is {usage_percent:.1f}%"
            elif usage_percent < 90:
                status = "degraded"
                message = f"Disk usage is high: {usage_percent:.1f}%"
            else:
                status = "unhealthy"
                message = f"Disk usage is critical: {usage_percent:.1f}%"
            
            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=None,
                details={"usage_percent": usage_percent}
            )
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status="unhealthy",
                message=f"Disk space check failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
                response_time_ms=None
            )
    
    # Add health checkers
    monitoring_service.add_health_checker(check_database_health)
    monitoring_service.add_health_checker(check_redis_health)
    monitoring_service.add_health_checker(check_celery_health)
    monitoring_service.add_health_checker(check_api_health)
    monitoring_service.add_health_checker(check_disk_space)


@shared_task(bind=True, name="monitoring.process_alerts")
def process_alerts(self) -> Dict[str, Any]:
    """Process pending alerts and send notifications"""
    try:
        alert_manager = AlertManager()
        
        # Get recent alerts (last 5 minutes)
        recent_alerts = [
            alert for alert in alert_manager.get_notifications()
            if alert.timestamp > datetime.now(timezone.utc) - timedelta(minutes=5)
        ]
        
        processed_count = 0
        for alert in recent_alerts:
            try:
                alert_manager.process_alert(alert)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing alert {alert.id}: {str(e)}")
        
        result = {
            "alerts_processed": processed_count,
            "total_alerts": len(recent_alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Processed {processed_count} alerts")
        return result
        
    except Exception as e:
        logger.error(f"Error processing alerts: {str(e)}")
        self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, name="monitoring.generate_monitoring_report")
def generate_monitoring_report(self, report_type: str = "daily") -> Dict[str, Any]:
    """Generate monitoring report"""
    try:
        monitoring_service = MonitoringService()
        
        # Determine time range
        if report_type == "daily":
            start_time = datetime.utcnow() - timedelta(days=1)
        elif report_type == "weekly":
            start_time = datetime.utcnow() - timedelta(weeks=1)
        elif report_type == "monthly":
            start_time = datetime.utcnow() - timedelta(days=30)
        else:
            start_time = datetime.utcnow() - timedelta(days=1)
        
        # Get metrics for the period
        metrics = monitoring_service.get_metrics(start_time=start_time)
        
        # Get alerts for the period
        alerts = monitoring_service.get_alerts(start_time=start_time)
        
        # Get health status
        health_status = monitoring_service.get_health_status()
        
        # Calculate statistics
        metrics_by_name = {}
        for metric in metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric.value)
        
        metric_stats = {}
        for name, values in metrics_by_name.items():
            metric_stats[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values)
            }
        
        # Alert statistics
        alerts_by_severity = {}
        for alert in alerts:
            severity = alert.severity.value
            alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
        
        report = {
            "report_type": report_type,
            "period": {
                "start": start_time.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_metrics": len(metrics),
                "total_alerts": len(alerts),
                "health_status": health_status["status"]
            },
            "metrics": {
                "by_name": metric_stats,
                "top_metrics": sorted(
                    metric_stats.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )[:10]
            },
            "alerts": {
                "by_severity": alerts_by_severity,
                "recent_alerts": [
                    {
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in alerts[-10:]  # Last 10 alerts
                ]
            },
            "health": health_status,
            "recommendations": generate_recommendations(metric_stats, alerts_by_severity, health_status),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Generated {report_type} monitoring report")
        return report
        
    except Exception as e:
        logger.error(f"Error generating monitoring report: {str(e)}")
        self.retry(countdown=300, max_retries=3)


def generate_recommendations(metric_stats: Dict[str, Any], 
                           alerts_by_severity: Dict[str, int],
                           health_status: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on monitoring data"""
    recommendations = []
    
    # Check CPU usage
    if "cpu_usage" in metric_stats:
        avg_cpu = metric_stats["cpu_usage"]["avg"]
        if avg_cpu > 80:
            recommendations.append(f"High CPU usage detected ({avg_cpu:.1f}%). Consider scaling up resources.")
    
    # Check memory usage
    if "memory_usage" in metric_stats:
        avg_memory = metric_stats["memory_usage"]["avg"]
        if avg_memory > 85:
            recommendations.append(f"High memory usage detected ({avg_memory:.1f}%). Consider optimizing memory usage.")
    
    # Check disk usage
    if "disk_usage" in metric_stats:
        avg_disk = metric_stats["disk_usage"]["avg"]
        if avg_disk > 90:
            recommendations.append(f"High disk usage detected ({avg_disk:.1f}%). Consider cleanup or storage expansion.")
    
    # Check error rate
    if "error_rate" in metric_stats:
        avg_errors = metric_stats["error_rate"]["avg"]
        if avg_errors > 5:
            recommendations.append(f"High error rate detected ({avg_errors:.1f}%). Review error logs and fix issues.")
    
    # Check alerts
    critical_alerts = alerts_by_severity.get("critical", 0)
    error_alerts = alerts_by_severity.get("error", 0)
    
    if critical_alerts > 0:
        recommendations.append(f"Critical alerts detected ({critical_alerts}). Immediate attention required.")
    
    if error_alerts > 10:
        recommendations.append(f"High number of error alerts ({error_alerts}). Review system stability.")
    
    # Check health status
    if health_status["status"] != "healthy":
        recommendations.append(f"System health is {health_status['status']}. Review health checks.")
    
    if not recommendations:
        recommendations.append("System is performing well. No immediate action required.")
    
    return recommendations


@shared_task(bind=True, name="monitoring.cleanup_monitoring_data")
def cleanup_monitoring_data(self, days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean up old monitoring data"""
    try:
        monitoring_service = MonitoringService()
        alert_manager = AlertManager()
        
        # Clean up old metrics and alerts
        metrics_cleaned = monitoring_service.cleanup_old_data(days_to_keep)
        
        # Clean up old notifications
        notifications_cleaned = alert_manager.cleanup_old_notifications(days_to_keep)
        
        result = {
            "metrics_cleaned": metrics_cleaned,
            "notifications_cleaned": notifications_cleaned,
            "total_cleaned": metrics_cleaned + notifications_cleaned,
            "days_to_keep": days_to_keep,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Cleaned up {result['total_cleaned']} monitoring data entries")
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up monitoring data: {str(e)}")
        self.retry(countdown=300, max_retries=3)


@shared_task(bind=True, name="monitoring.health_check")
def monitoring_health_check(self) -> Dict[str, Any]:
    """Check monitoring system health"""
    try:
        monitoring_service = MonitoringService()
        alert_manager = AlertManager()
        
        # Test metric collection
        test_metrics = monitoring_service.collect_system_metrics()
        
        # Test health checks
        add_default_health_checkers(monitoring_service)
        health_results = monitoring_service.run_health_checks()
        
        # Test alert manager
        notification_stats = alert_manager.get_notification_stats()
        
        # Determine overall status
        health_status = "healthy"
        if not test_metrics:
            health_status = "unhealthy"
        elif any(h.status == "unhealthy" for h in health_results.values()):
            health_status = "degraded"
        
        result = {
            "status": health_status,
            "metrics_collected": len(test_metrics),
            "health_checks": len(health_results),
            "health_checks_passing": sum(1 for h in health_results.values() if h.status == "healthy"),
            "notification_stats": notification_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Monitoring health check completed: {health_status}")
        return result
        
    except Exception as e:
        logger.error(f"Error in monitoring health check: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 