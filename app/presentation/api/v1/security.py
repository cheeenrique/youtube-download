from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.infrastructure.security.security_service import SecurityService, SecurityLevel
from app.infrastructure.security.rate_limiter import RateLimiter, RateLimitConfig, RateLimitStrategy
from app.infrastructure.security.input_validator import InputValidator, ValidationLevel
from app.presentation.schemas.security import (
    TokenRequest, TokenResponse, ValidationRequest, ValidationResponse,
    SecurityEventResponse, SecurityStatsResponse, RateLimitInfo,
    SecurityReportRequest, SecurityReportResponse, SecurityHealthResponse,
    BlockIPRequest, UnblockIPRequest, SecurityAlertResponse
)
from app.shared.config import settings
from app.infrastructure.celery.tasks.security_tasks import (
    monitor_security_events, cleanup_security_data, analyze_threat_patterns,
    auto_block_suspicious_ips, generate_security_report, validate_input_batch,
    security_health_check
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security"])
security = HTTPBearer()

# Initialize services
# settings já importado globalmente
security_service = SecurityService(settings.secret_key)
rate_limiter = RateLimiter()
input_validator = InputValidator()

# Setup default rate limits
rate_limiter.add_limit("api", RateLimitConfig(
    max_requests=1000,
    window_seconds=3600,
    strategy=RateLimitStrategy.SLIDING_WINDOW
))

rate_limiter.add_limit("auth", RateLimitConfig(
    max_requests=10,
    window_seconds=300,
    strategy=RateLimitStrategy.SLIDING_WINDOW
))


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = security_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload


def check_rate_limit(request: Request, limit_name: str = "api") -> bool:
    """Check rate limit for request"""
    client_ip = request.client.host
    identifier = f"{client_ip}_{limit_name}"
    
    result = rate_limiter.check_limit(limit_name, identifier)
    
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {int(result.retry_after)} seconds.",
            headers={"Retry-After": str(int(result.retry_after)) if result.retry_after else "60"}
        )
    
    return True


@router.post("/token", response_model=TokenResponse)
async def generate_token(request: TokenRequest, req: Request):
    """Generate JWT token for authentication"""
    # Check rate limit for auth endpoints
    check_rate_limit(req, "auth")
    
    # Validate input
    validation_result = input_validator.validate_and_sanitize_input(
        request.username, "username"
    )
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid username: {', '.join(validation_result.errors)}"
        )
    
    # In a real application, you would verify credentials against a database
    # For demo purposes, we'll accept any username/password combination
    if not request.username or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    # Generate token
    token = security_service.generate_token(request.username, expires_in=request.expires_in)
    
    # Log security event
    security_service._log_security_event(
        "token_generated", SecurityLevel.LOW, request.username, req.client.host
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=request.expires_in,
        user_id=request.username
    )


@router.post("/validate", response_model=ValidationResponse)
async def validate_input(request: ValidationRequest, req: Request):
    """Validate input data"""
    check_rate_limit(req)
    
    results = []
    for input_data in request.inputs:
        if input_data.type == "url":
            result = input_validator.validate_url(
                input_data.value, 
                ValidationLevel.STRICT if input_data.strict else ValidationLevel.NORMAL
            )
        elif input_data.type == "email":
            result = input_validator.validate_email(input_data.value)
        elif input_data.type == "filename":
            result = input_validator.validate_filename(input_data.value)
        else:
            result = input_validator.validate_and_sanitize_input(
                input_data.value, input_data.type
            )
        
        results.append({
            "input": input_data.dict(),
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "sanitized_value": result.sanitized_value
        })
    
    return ValidationResponse(
        total_inputs=len(request.inputs),
        valid_inputs=sum(1 for r in results if r["is_valid"]),
        results=results
    )


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    severity: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Get security events"""
    check_rate_limit(req)
    
    # Convert severity string to enum
    severity_enum = None
    if severity:
        try:
            severity_enum = SecurityLevel(severity.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity level: {severity}"
            )
    
    events = security_service.get_security_events(
        severity=severity_enum,
        start_time=start_time,
        end_time=end_time
    )
    
    # Limit results
    events = events[-limit:] if limit > 0 else events
    
    return [
        SecurityEventResponse(
            event_type=event.event_type,
            severity=event.severity.value,
            user_id=event.user_id,
            ip_address=event.ip_address,
            timestamp=event.timestamp,
            details=event.details,
            resource=event.resource
        )
        for event in events
    ]


@router.get("/stats", response_model=SecurityStatsResponse)
async def get_security_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Get security statistics"""
    check_rate_limit(req)
    
    stats = security_service.get_security_stats()
    
    return SecurityStatsResponse(
        total_events=stats["total_events"],
        events_by_severity=stats["events_by_severity"],
        events_by_type=stats["events_by_type"],
        blocked_ips_count=stats["blocked_ips_count"],
        rate_limited_identifiers=stats["rate_limited_identifiers"]
    )


@router.get("/rate-limit/{identifier}", response_model=RateLimitInfo)
async def get_rate_limit_info(
    identifier: str,
    limit_name: str = "api",
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Get rate limit information for an identifier"""
    check_rate_limit(req)
    
    info = rate_limiter.get_limit_info(limit_name, identifier)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rate limit '{limit_name}' not found"
        )
    
    return RateLimitInfo(**info)


@router.post("/block-ip")
async def block_ip(
    request: BlockIPRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Block an IP address"""
    check_rate_limit(req)
    
    # Validate IP address format
    ip_validation = input_validator.validate_and_sanitize_input(request.ip_address, "ip")
    if not ip_validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid IP address: {', '.join(ip_validation.errors)}"
        )
    
    security_service.block_ip(request.ip_address, request.duration_minutes)
    
    return {
        "message": f"IP {request.ip_address} blocked for {request.duration_minutes} minutes",
        "ip_address": request.ip_address,
        "blocked_until": datetime.utcnow() + timedelta(minutes=request.duration_minutes)
    }


@router.post("/unblock-ip")
async def unblock_ip(
    request: UnblockIPRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Unblock an IP address"""
    check_rate_limit(req)
    
    security_service.unblock_ip(request.ip_address)
    
    return {
        "message": f"IP {request.ip_address} unblocked",
        "ip_address": request.ip_address
    }


@router.post("/monitor", response_model=Dict[str, Any])
async def trigger_security_monitoring(
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Trigger security monitoring task"""
    check_rate_limit(req)
    
    task = monitor_security_events.delay()
    
    return {
        "message": "Security monitoring task started",
        "task_id": task.id
    }


@router.post("/cleanup")
async def trigger_security_cleanup(
    days_to_keep: int = 30,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Trigger security data cleanup"""
    check_rate_limit(req)
    
    task = cleanup_security_data.delay(days_to_keep)
    
    return {
        "message": f"Security cleanup task started (keeping {days_to_keep} days of data)",
        "task_id": task.id
    }


@router.post("/analyze-threats", response_model=Dict[str, Any])
async def trigger_threat_analysis(
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Trigger threat pattern analysis"""
    check_rate_limit(req)
    
    task = analyze_threat_patterns.delay()
    
    return {
        "message": "Threat analysis task started",
        "task_id": task.id
    }


@router.post("/auto-block", response_model=Dict[str, Any])
async def trigger_auto_block(
    threshold: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Trigger automatic IP blocking"""
    check_rate_limit(req)
    
    task = auto_block_suspicious_ips.delay(threshold)
    
    return {
        "message": f"Auto-block task started with threshold {threshold}",
        "task_id": task.id
    }


@router.post("/report", response_model=SecurityReportResponse)
async def generate_report(
    request: SecurityReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Generate security report"""
    check_rate_limit(req)
    
    task = generate_security_report.delay(request.report_type)
    
    return SecurityReportResponse(
        message=f"Security report generation started ({request.report_type})",
        task_id=task.id,
        report_type=request.report_type
    )


@router.post("/validate-batch", response_model=ValidationResponse)
async def validate_input_batch_endpoint(
    request: ValidationRequest,
    req: Request = None
):
    """Validate a batch of inputs using Celery task"""
    check_rate_limit(req)
    
    # Convert to format expected by Celery task
    inputs = []
    for input_data in request.inputs:
        inputs.append({
            "type": input_data.type,
            "value": input_data.value,
            "level": "strict" if input_data.strict else "normal"
        })
    
    task = validate_input_batch.delay(inputs)
    
    return ValidationResponse(
        message="Batch validation task started",
        task_id=task.id,
        total_inputs=len(request.inputs)
    )


@router.get("/health", response_model=SecurityHealthResponse)
async def security_health_check_endpoint(req: Request = None):
    """Check security system health"""
    check_rate_limit(req)
    
    task = security_health_check.delay()
    
    return SecurityHealthResponse(
        message="Security health check started",
        task_id=task.id
    )


@router.get("/alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    severity: Optional[str] = None,
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
    req: Request = None
):
    """Get recent security alerts"""
    check_rate_limit(req)
    
    # Get recent high-severity events
    recent_events = security_service.get_security_events(
        severity=SecurityLevel.HIGH if severity == "high" else None,
        start_time=datetime.utcnow() - timedelta(hours=24)
    )
    
    alerts = []
    for event in recent_events[-limit:]:
        if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            alerts.append(SecurityAlertResponse(
                type=event.event_type,
                severity=event.severity.value,
                message=f"{event.event_type} from {event.ip_address}",
                timestamp=event.timestamp,
                ip_address=event.ip_address,
                user_id=event.user_id,
                resource=event.resource
            ))
    
    return alerts


@router.post("/test-auth")
async def test_authentication(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Test authentication endpoint"""
    return {
        "message": "Authentication successful",
        "user_id": current_user.get("user_id"),
        "expires_at": datetime.fromtimestamp(current_user.get("exp")).isoformat()
    } 