from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.infrastructure.monitoring.monitoring_service import (
    MonitoringService, Metric, MetricType, AlertSeverity, HealthCheck
)
from app.infrastructure.monitoring.alert_manager import (
    AlertManager, NotificationChannel, NotificationConfig
)
from app.presentation.schemas.monitoring import (
    MetricResponse, HealthCheckResponse, AlertResponse, MonitoringStatsResponse,
    MonitoringReportRequest, MonitoringReportResponse, NotificationConfigRequest,
    NotificationConfigResponse, MonitoringHealthResponse, MetricStatsResponse,
    AlertStatsResponse, NotificationStatsResponse
)
from app.shared.config import settings
from app.infrastructure.celery.tasks.monitoring_tasks import (
    collect_system_metrics, run_health_checks, process_alerts,
    generate_monitoring_report, cleanup_monitoring_data, monitoring_health_check
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])
security = HTTPBearer()

# Initialize services
# settings já importado globalmente
monitoring_service = MonitoringService()
alert_manager = AlertManager()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    # Simplified authentication for monitoring endpoints
    # In production, you'd verify the token properly
    return {"user_id": "monitoring_user"}


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    metric_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get monitoring metrics"""
    metrics = monitoring_service.get_metrics(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time
    )
    
    # Limit results
    metrics = metrics[-limit:] if limit > 0 else metrics
    
    return [
        MetricResponse(
            name=metric.name,
            value=metric.value,
            type=metric.type.value,
            timestamp=metric.timestamp,
            labels=metric.labels,
            description=metric.description
        )
        for metric in metrics
    ]


@router.get("/metrics/{metric_name}/stats", response_model=MetricStatsResponse)
async def get_metric_stats(
    metric_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get statistics for a specific metric"""
    stats = monitoring_service.get_metric_stats(
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time
    )
    
    return MetricStatsResponse(**stats)


@router.get("/health", response_model=HealthCheckResponse)
async def get_health_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get system health status"""
    health_status = monitoring_service.get_health_status()
    
    return HealthCheckResponse(
        status=health_status["status"],
        message=health_status["message"],
        checks_count=health_status["checks_count"],
        healthy_count=health_status["healthy_count"],
        unhealthy_count=health_status["unhealthy_count"],
        degraded_count=health_status["degraded_count"],
        checks=health_status["checks"]
    )


@router.post("/health/check")
async def trigger_health_checks(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Trigger health checks"""
    task = run_health_checks.delay()
    
    return {
        "message": "Health checks started",
        "task_id": task.id
    }


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get monitoring alerts"""
    # Convert severity string to enum
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity level: {severity}"
            )
    
    alerts = monitoring_service.get_alerts(
        severity=severity_enum,
        resolved=resolved,
        start_time=start_time
    )
    
    # Limit results
    alerts = alerts[-limit:] if limit > 0 else alerts
    
    return [
        AlertResponse(
            id=alert.id,
            name=alert.name,
            severity=alert.severity.value,
            message=alert.message,
            timestamp=alert.timestamp,
            source=alert.source,
            metric_name=alert.metric_name,
            metric_value=alert.metric_value,
            threshold=alert.threshold,
            resolved=alert.resolved,
            resolved_at=alert.resolved_at
        )
        for alert in alerts
    ]


@router.get("/alerts/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    start_time: Optional[datetime] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get alert statistics"""
    alerts = monitoring_service.get_alerts(start_time=start_time)
    
    # Calculate statistics
    total_alerts = len(alerts)
    active_alerts = len([a for a in alerts if not a.resolved])
    resolved_alerts = len([a for a in alerts if a.resolved])
    
    alerts_by_severity = {}
    for alert in alerts:
        severity = alert.severity.value
        alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
    
    alerts_by_source = {}
    for alert in alerts:
        source = alert.source
        alerts_by_source[source] = alerts_by_source.get(source, 0) + 1
    
    return AlertStatsResponse(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        resolved_alerts=resolved_alerts,
        alerts_by_severity=alerts_by_severity,
        alerts_by_source=alerts_by_source
    )


@router.post("/alerts/process")
async def trigger_alert_processing(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Trigger alert processing"""
    task = process_alerts.delay()
    
    return {
        "message": "Alert processing started",
        "task_id": task.id
    }


@router.get("/stats", response_model=MonitoringStatsResponse)
async def get_monitoring_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get monitoring statistics"""
    stats = monitoring_service.get_monitoring_summary()
    
    return MonitoringStatsResponse(
        metrics_count=stats["metrics_count"],
        active_alerts_count=stats["active_alerts_count"],
        alerts_by_severity=stats["alerts_by_severity"],
        health_status=stats["health_status"],
        monitoring_enabled=stats["monitoring_enabled"],
        timestamp=stats["timestamp"]
    )


@router.post("/metrics/collect")
async def trigger_metric_collection(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Trigger metric collection"""
    task = collect_system_metrics.delay()
    
    return {
        "message": "Metric collection started",
        "task_id": task.id
    }


@router.post("/report", response_model=MonitoringReportResponse)
async def generate_report(
    request: MonitoringReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate monitoring report"""
    task = generate_monitoring_report.delay(request.report_type)
    
    return MonitoringReportResponse(
        message=f"Monitoring report generation started ({request.report_type})",
        task_id=task.id,
        report_type=request.report_type
    )


@router.post("/cleanup")
async def trigger_cleanup(
    days_to_keep: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Trigger monitoring data cleanup"""
    task = cleanup_monitoring_data.delay(days_to_keep)
    
    return {
        "message": f"Monitoring cleanup started (keeping {days_to_keep} days of data)",
        "task_id": task.id
    }


@router.get("/health/check", response_model=MonitoringHealthResponse)
async def monitoring_health_check_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Check monitoring system health"""
    task = monitoring_health_check.delay()
    
    return MonitoringHealthResponse(
        message="Monitoring health check started",
        task_id=task.id
    )


@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications(
    channel: Optional[str] = None,
    start_time: Optional[datetime] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get notification history"""
    # Convert channel string to enum
    channel_enum = None
    if channel:
        try:
            channel_enum = NotificationChannel(channel.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid notification channel: {channel}"
            )
    
    notifications = alert_manager.get_notifications(
        channel=channel_enum,
        start_time=start_time
    )
    
    # Limit results
    notifications = notifications[-limit:] if limit > 0 else notifications
    
    return [
        {
            "id": n.id,
            "channel": n.channel.value,
            "recipient": n.recipient,
            "subject": n.subject,
            "message": n.message,
            "timestamp": n.timestamp,
            "sent": n.sent,
            "error": n.error
        }
        for n in notifications
    ]


@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get notification statistics"""
    stats = alert_manager.get_notification_stats()
    
    return NotificationStatsResponse(
        total_notifications=stats["total_notifications"],
        sent_notifications=stats["sent_notifications"],
        failed_notifications=stats["failed_notifications"],
        success_rate=stats["success_rate"],
        by_channel=stats["by_channel"]
    )


@router.get("/config/notifications", response_model=List[NotificationConfigResponse])
async def get_notification_configs(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get notification configurations"""
    configs = []
    
    for channel, config in alert_manager.notification_configs.items():
        configs.append(NotificationConfigResponse(
            channel=config.channel.value,
            enabled=config.enabled,
            recipients=config.recipients,
            webhook_url=config.webhook_url,
            bot_token=config.bot_token,
            chat_id=config.chat_id,
            severity_filter=[s.value for s in config.severity_filter] if config.severity_filter else None,
            rate_limit_minutes=config.rate_limit_minutes
        ))
    
    return configs


@router.post("/config/notifications")
async def update_notification_config(
    request: NotificationConfigRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update notification configuration"""
    try:
        channel = NotificationChannel(request.channel.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid notification channel: {request.channel}"
        )
    
    # Convert severity filter strings to enums
    severity_filter = None
    if request.severity_filter:
        try:
            severity_filter = [AlertSeverity(s.lower()) for s in request.severity_filter]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity level in filter: {str(e)}"
            )
    
    config = NotificationConfig(
        channel=channel,
        enabled=request.enabled,
        recipients=request.recipients,
        webhook_url=request.webhook_url,
        bot_token=request.bot_token,
        chat_id=request.chat_id,
        severity_filter=severity_filter,
        rate_limit_minutes=request.rate_limit_minutes
    )
    
    alert_manager.add_notification_config(config)
    
    return {
        "message": f"Notification configuration updated for {channel.value}",
        "channel": channel.value
    }


@router.delete("/config/notifications/{channel}")
async def remove_notification_config(
    channel: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove notification configuration"""
    try:
        channel_enum = NotificationChannel(channel.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid notification channel: {channel}"
        )
    
    alert_manager.remove_notification_config(channel_enum)
    
    return {
        "message": f"Notification configuration removed for {channel}",
        "channel": channel
    }


@router.post("/thresholds/{metric_name}")
async def set_alert_threshold(
    metric_name: str,
    severity: str,
    threshold: float,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Set alert threshold for a metric"""
    try:
        severity_enum = AlertSeverity(severity.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity level: {severity}"
        )
    
    monitoring_service.set_alert_threshold(metric_name, severity, threshold)
    
    return {
        "message": f"Alert threshold set for {metric_name}",
        "metric_name": metric_name,
        "severity": severity,
        "threshold": threshold
    }


@router.get("/thresholds")
async def get_alert_thresholds(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all alert thresholds"""
    return {
        "thresholds": monitoring_service.alert_thresholds,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/start")
async def start_monitoring(
    interval_seconds: int = 60,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start continuous monitoring"""
    if interval_seconds < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monitoring interval must be at least 10 seconds"
        )
    
    monitoring_service.start_monitoring(interval_seconds)
    
    return {
        "message": f"Monitoring started with {interval_seconds}s interval",
        "interval_seconds": interval_seconds
    }


@router.post("/stop")
async def stop_monitoring(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Stop continuous monitoring"""
    monitoring_service.stop_monitoring_service()
    
    return {
        "message": "Monitoring stopped"
    }


@router.get("/status")
async def get_monitoring_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get monitoring service status"""
    return {
        "monitoring_enabled": monitoring_service.monitoring_enabled,
        "monitoring_thread_alive": monitoring_service.monitoring_thread.is_alive() if monitoring_service.monitoring_thread else False,
        "metrics_count": sum(len(metrics) for metrics in monitoring_service.metrics.values()),
        "alerts_count": len(monitoring_service.alerts),
        "health_checks_count": len(monitoring_service.health_checks),
        "notification_configs_count": len(alert_manager.notification_configs),
        "timestamp": datetime.utcnow().isoformat()
    } 