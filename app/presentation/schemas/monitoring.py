from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    CONSOLE = "console"
    LOG = "log"


class MetricResponse(BaseModel):
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    type: str = Field(..., description="Metric type")
    timestamp: datetime = Field(..., description="Metric timestamp")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")
    description: Optional[str] = Field(None, description="Metric description")


class MetricStatsResponse(BaseModel):
    metric_name: str = Field(..., description="Metric name")
    count: int = Field(..., description="Number of metric values")
    min: Optional[float] = Field(None, description="Minimum value")
    max: Optional[float] = Field(None, description="Maximum value")
    avg: Optional[float] = Field(None, description="Average value")
    median: Optional[float] = Field(None, description="Median value")
    std_dev: Optional[float] = Field(None, description="Standard deviation")
    latest_value: Optional[float] = Field(None, description="Latest metric value")
    latest_timestamp: Optional[datetime] = Field(None, description="Latest metric timestamp")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    message: str = Field(..., description="Health status message")
    checks_count: int = Field(..., description="Total number of health checks")
    healthy_count: int = Field(..., description="Number of healthy checks")
    unhealthy_count: int = Field(..., description="Number of unhealthy checks")
    degraded_count: int = Field(..., description="Number of degraded checks")
    checks: List[Dict[str, Any]] = Field(..., description="Detailed health check results")


class AlertResponse(BaseModel):
    id: str = Field(..., description="Alert ID")
    name: str = Field(..., description="Alert name")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(..., description="Alert timestamp")
    source: str = Field(..., description="Alert source")
    metric_name: Optional[str] = Field(None, description="Related metric name")
    metric_value: Optional[float] = Field(None, description="Metric value that triggered alert")
    threshold: Optional[float] = Field(None, description="Alert threshold")
    resolved: bool = Field(..., description="Whether alert is resolved")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")


class AlertStatsResponse(BaseModel):
    total_alerts: int = Field(..., description="Total number of alerts")
    active_alerts: int = Field(..., description="Number of active alerts")
    resolved_alerts: int = Field(..., description="Number of resolved alerts")
    alerts_by_severity: Dict[str, int] = Field(..., description="Alerts grouped by severity")
    alerts_by_source: Dict[str, int] = Field(..., description="Alerts grouped by source")


class MonitoringStatsResponse(BaseModel):
    metrics_count: int = Field(..., description="Number of recent metrics")
    active_alerts_count: int = Field(..., description="Number of active alerts")
    alerts_by_severity: Dict[str, int] = Field(..., description="Active alerts by severity")
    health_status: Dict[str, Any] = Field(..., description="Health status information")
    monitoring_enabled: bool = Field(..., description="Whether monitoring is enabled")
    timestamp: str = Field(..., description="Statistics timestamp")


class MonitoringReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to generate")


class MonitoringReportResponse(BaseModel):
    message: str = Field(..., description="Response message")
    task_id: str = Field(..., description="Celery task ID")
    report_type: str = Field(..., description="Type of report being generated")


class MonitoringHealthResponse(BaseModel):
    message: str = Field(..., description="Response message")
    task_id: str = Field(..., description="Celery task ID")


class NotificationConfigRequest(BaseModel):
    channel: str = Field(..., description="Notification channel")
    enabled: bool = Field(default=True, description="Whether channel is enabled")
    recipients: Optional[List[str]] = Field(None, description="Email recipients")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    bot_token: Optional[str] = Field(None, description="Bot token for messaging platforms")
    chat_id: Optional[str] = Field(None, description="Chat ID for messaging platforms")
    severity_filter: Optional[List[str]] = Field(None, description="Severity levels to notify")
    rate_limit_minutes: int = Field(default=5, description="Rate limit in minutes")


class NotificationConfigResponse(BaseModel):
    channel: str = Field(..., description="Notification channel")
    enabled: bool = Field(..., description="Whether channel is enabled")
    recipients: Optional[List[str]] = Field(None, description="Email recipients")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    bot_token: Optional[str] = Field(None, description="Bot token for messaging platforms")
    chat_id: Optional[str] = Field(None, description="Chat ID for messaging platforms")
    severity_filter: Optional[List[str]] = Field(None, description="Severity levels to notify")
    rate_limit_minutes: int = Field(..., description="Rate limit in minutes")


class NotificationStatsResponse(BaseModel):
    total_notifications: int = Field(..., description="Total number of notifications")
    sent_notifications: int = Field(..., description="Number of sent notifications")
    failed_notifications: int = Field(..., description="Number of failed notifications")
    success_rate: float = Field(..., description="Notification success rate")
    by_channel: Dict[str, Dict[str, int]] = Field(..., description="Statistics by channel")


class MonitoringConfigRequest(BaseModel):
    monitoring_enabled: bool = Field(..., description="Whether monitoring is enabled")
    collection_interval: int = Field(..., description="Metric collection interval in seconds")
    health_check_interval: int = Field(..., description="Health check interval in seconds")
    alert_processing_interval: int = Field(..., description="Alert processing interval in seconds")
    data_retention_days: int = Field(..., description="Data retention period in days")


class MonitoringConfigResponse(BaseModel):
    monitoring_enabled: bool = Field(..., description="Whether monitoring is enabled")
    collection_interval: int = Field(..., description="Metric collection interval in seconds")
    health_check_interval: int = Field(..., description="Health check interval in seconds")
    alert_processing_interval: int = Field(..., description="Alert processing interval in seconds")
    data_retention_days: int = Field(..., description="Data retention period in days")
    timestamp: str = Field(..., description="Configuration timestamp")


class MetricCollectionRequest(BaseModel):
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    type: str = Field(..., description="Metric type")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")
    description: Optional[str] = Field(None, description="Metric description")


class HealthCheckRequest(BaseModel):
    name: str = Field(..., description="Health check name")
    status: str = Field(..., description="Health check status")
    message: str = Field(..., description="Health check message")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class AlertRequest(BaseModel):
    name: str = Field(..., description="Alert name")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    source: str = Field(..., description="Alert source")
    metric_name: Optional[str] = Field(None, description="Related metric name")
    metric_value: Optional[float] = Field(None, description="Metric value")
    threshold: Optional[float] = Field(None, description="Alert threshold")


class MonitoringDashboardResponse(BaseModel):
    overview: Dict[str, Any] = Field(..., description="Monitoring overview")
    metrics: List[Dict[str, Any]] = Field(..., description="Recent metrics")
    alerts: List[Dict[str, Any]] = Field(..., description="Recent alerts")
    health_checks: List[Dict[str, Any]] = Field(..., description="Health check results")
    notifications: List[Dict[str, Any]] = Field(..., description="Recent notifications")
    timestamp: str = Field(..., description="Dashboard timestamp")


class MonitoringExportRequest(BaseModel):
    data_type: str = Field(..., description="Type of data to export")
    start_time: Optional[datetime] = Field(None, description="Start time for export")
    end_time: Optional[datetime] = Field(None, description="End time for export")
    format: str = Field(default="json", description="Export format")


class MonitoringExportResponse(BaseModel):
    message: str = Field(..., description="Export message")
    task_id: str = Field(..., description="Celery task ID")
    data_type: str = Field(..., description="Type of data being exported")
    format: str = Field(..., description="Export format")


class MonitoringTestRequest(BaseModel):
    test_type: str = Field(..., description="Type of test to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Test parameters")


class MonitoringTestResponse(BaseModel):
    test_type: str = Field(..., description="Type of test performed")
    status: str = Field(..., description="Test status")
    results: Dict[str, Any] = Field(..., description="Test results")
    timestamp: str = Field(..., description="Test timestamp")
    duration_ms: Optional[int] = Field(None, description="Test duration in milliseconds")


class MonitoringMaintenanceRequest(BaseModel):
    operation: str = Field(..., description="Maintenance operation")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class MonitoringMaintenanceResponse(BaseModel):
    operation: str = Field(..., description="Maintenance operation performed")
    status: str = Field(..., description="Operation status")
    results: Dict[str, Any] = Field(..., description="Operation results")
    timestamp: str = Field(..., description="Operation timestamp")


class MonitoringPerformanceRequest(BaseModel):
    metric_name: str = Field(..., description="Metric to analyze")
    time_range: str = Field(..., description="Time range for analysis")
    analysis_type: str = Field(..., description="Type of analysis")


class MonitoringPerformanceResponse(BaseModel):
    metric_name: str = Field(..., description="Analyzed metric")
    time_range: str = Field(..., description="Analysis time range")
    analysis_type: str = Field(..., description="Type of analysis performed")
    results: Dict[str, Any] = Field(..., description="Analysis results")
    recommendations: List[str] = Field(..., description="Performance recommendations")
    timestamp: str = Field(..., description="Analysis timestamp") 