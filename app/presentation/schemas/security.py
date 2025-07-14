from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationLevel(str, Enum):
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


class TokenRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Username for authentication")
    password: str = Field(..., min_length=1, description="Password for authentication")
    expires_in: int = Field(default=3600, ge=300, le=86400, description="Token expiration time in seconds")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: str = Field(..., description="User ID")


class InputData(BaseModel):
    type: str = Field(..., description="Type of input to validate")
    value: str = Field(..., description="Value to validate")
    strict: bool = Field(default=False, description="Use strict validation")


class ValidationRequest(BaseModel):
    inputs: List[InputData] = Field(..., description="List of inputs to validate")


class ValidationResult(BaseModel):
    input: Dict[str, Any] = Field(..., description="Original input data")
    is_valid: bool = Field(..., description="Whether the input is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    sanitized_value: Optional[str] = Field(None, description="Sanitized value if applicable")


class ValidationResponse(BaseModel):
    total_inputs: int = Field(..., description="Total number of inputs")
    valid_inputs: int = Field(..., description="Number of valid inputs")
    results: List[ValidationResult] = Field(..., description="Validation results")
    message: Optional[str] = Field(None, description="Additional message")
    task_id: Optional[str] = Field(None, description="Celery task ID for async operations")


class SecurityEventResponse(BaseModel):
    event_type: str = Field(..., description="Type of security event")
    severity: str = Field(..., description="Event severity level")
    user_id: Optional[str] = Field(None, description="User ID associated with the event")
    ip_address: str = Field(..., description="IP address associated with the event")
    timestamp: datetime = Field(..., description="Event timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
    resource: Optional[str] = Field(None, description="Resource associated with the event")


class SecurityStatsResponse(BaseModel):
    total_events: int = Field(..., description="Total number of security events")
    events_by_severity: Dict[str, int] = Field(..., description="Events grouped by severity")
    events_by_type: Dict[str, int] = Field(..., description="Events grouped by type")
    blocked_ips_count: int = Field(..., description="Number of currently blocked IPs")
    rate_limited_identifiers: int = Field(..., description="Number of rate-limited identifiers")


class RateLimitInfo(BaseModel):
    requests: Optional[int] = Field(None, description="Current number of requests")
    max_requests: int = Field(..., description="Maximum allowed requests")
    window_seconds: int = Field(..., description="Time window in seconds")
    tokens: Optional[int] = Field(None, description="Current tokens (for token bucket)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens (for token bucket)")
    refill_rate: Optional[float] = Field(None, description="Token refill rate (for token bucket)")


class BlockIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to block")
    duration_minutes: int = Field(default=60, ge=1, le=1440, description="Block duration in minutes")


class UnblockIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to unblock")


class SecurityReportRequest(BaseModel):
    report_type: str = Field(..., description="Type of report to generate")


class SecurityReportResponse(BaseModel):
    message: str = Field(..., description="Response message")
    task_id: str = Field(..., description="Celery task ID")
    report_type: str = Field(..., description="Type of report being generated")


class SecurityHealthResponse(BaseModel):
    message: str = Field(..., description="Response message")
    task_id: str = Field(..., description="Celery task ID")


class SecurityAlertResponse(BaseModel):
    type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(..., description="Alert timestamp")
    ip_address: Optional[str] = Field(None, description="IP address associated with alert")
    user_id: Optional[str] = Field(None, description="User ID associated with alert")
    resource: Optional[str] = Field(None, description="Resource associated with alert")


class ThreatAnalysisRequest(BaseModel):
    time_range_hours: int = Field(default=24, ge=1, le=168, description="Time range for analysis in hours")


class ThreatAnalysisResponse(BaseModel):
    total_events: int = Field(..., description="Total events analyzed")
    brute_force_attempts: int = Field(..., description="Number of brute force attempts")
    suspicious_ips_count: int = Field(..., description="Number of suspicious IPs")
    suspicious_ips: List[str] = Field(..., description="List of suspicious IP addresses")
    attack_types: Dict[str, int] = Field(..., description="Attack types and their counts")
    peak_attack_hours: List[tuple] = Field(..., description="Peak attack hours")
    top_targeted_resources: List[tuple] = Field(..., description="Most targeted resources")
    timestamp: datetime = Field(..., description="Analysis timestamp")


class SecurityConfigRequest(BaseModel):
    rate_limit_config: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")
    validation_config: Optional[Dict[str, Any]] = Field(None, description="Input validation configuration")
    monitoring_config: Optional[Dict[str, Any]] = Field(None, description="Security monitoring configuration")


class SecurityConfigResponse(BaseModel):
    rate_limit_config: Dict[str, Any] = Field(..., description="Current rate limiting configuration")
    validation_config: Dict[str, Any] = Field(..., description="Current input validation configuration")
    monitoring_config: Dict[str, Any] = Field(..., description="Current security monitoring configuration")


class SecurityMetricsRequest(BaseModel):
    metric_type: str = Field(..., description="Type of metrics to retrieve")
    time_range: str = Field(default="24h", description="Time range for metrics")


class SecurityMetricsResponse(BaseModel):
    metric_type: str = Field(..., description="Type of metrics")
    time_range: str = Field(..., description="Time range for metrics")
    data: Dict[str, Any] = Field(..., description="Metrics data")
    timestamp: datetime = Field(..., description="Metrics timestamp")


class SecurityAuditRequest(BaseModel):
    action: str = Field(..., description="Audit action")
    resource: Optional[str] = Field(None, description="Resource being audited")
    user_id: Optional[str] = Field(None, description="User performing the action")


class SecurityAuditResponse(BaseModel):
    audit_id: str = Field(..., description="Unique audit ID")
    action: str = Field(..., description="Audited action")
    resource: Optional[str] = Field(None, description="Resource that was audited")
    user_id: Optional[str] = Field(None, description="User who performed the action")
    timestamp: datetime = Field(..., description="Audit timestamp")
    status: str = Field(..., description="Audit status")


class SecurityTestRequest(BaseModel):
    test_type: str = Field(..., description="Type of security test to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Test parameters")


class SecurityTestResponse(BaseModel):
    test_type: str = Field(..., description="Type of security test performed")
    status: str = Field(..., description="Test status")
    results: Dict[str, Any] = Field(..., description="Test results")
    timestamp: datetime = Field(..., description="Test timestamp")
    duration_ms: Optional[int] = Field(None, description="Test duration in milliseconds")


class SecurityIncidentRequest(BaseModel):
    incident_type: str = Field(..., description="Type of security incident")
    severity: SecurityLevel = Field(..., description="Incident severity")
    description: str = Field(..., description="Incident description")
    affected_resources: Optional[List[str]] = Field(None, description="Affected resources")
    ip_addresses: Optional[List[str]] = Field(None, description="IP addresses involved")


class SecurityIncidentResponse(BaseModel):
    incident_id: str = Field(..., description="Unique incident ID")
    incident_type: str = Field(..., description="Type of security incident")
    severity: str = Field(..., description="Incident severity")
    description: str = Field(..., description="Incident description")
    status: str = Field(..., description="Incident status")
    created_at: datetime = Field(..., description="Incident creation timestamp")
    affected_resources: Optional[List[str]] = Field(None, description="Affected resources")
    ip_addresses: Optional[List[str]] = Field(None, description="IP addresses involved")
    assigned_to: Optional[str] = Field(None, description="User assigned to handle the incident")


class SecurityPolicyRequest(BaseModel):
    policy_name: str = Field(..., description="Name of the security policy")
    policy_type: str = Field(..., description="Type of security policy")
    rules: Dict[str, Any] = Field(..., description="Policy rules")
    enabled: bool = Field(default=True, description="Whether the policy is enabled")


class SecurityPolicyResponse(BaseModel):
    policy_id: str = Field(..., description="Unique policy ID")
    policy_name: str = Field(..., description="Name of the security policy")
    policy_type: str = Field(..., description="Type of security policy")
    rules: Dict[str, Any] = Field(..., description="Policy rules")
    enabled: bool = Field(..., description="Whether the policy is enabled")
    created_at: datetime = Field(..., description="Policy creation timestamp")
    updated_at: datetime = Field(..., description="Policy last update timestamp")
    applied_count: int = Field(..., description="Number of times policy was applied") 