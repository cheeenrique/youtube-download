from celery import shared_task
from datetime import datetime, timedelta, timezone
import logging
from typing import List, Dict, Any, Optional
import json

from app.infrastructure.security.security_service import SecurityService, SecurityLevel, SecurityEvent
from app.infrastructure.security.rate_limiter import RateLimiter
from app.infrastructure.security.input_validator import InputValidator
from app.shared.config import settings
from app.infrastructure.cache.mock_cache import mock_cache as redis_cache
from app.infrastructure.cache.analytics_cache import analytics_cache

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="security.monitor_security_events")
def monitor_security_events(self) -> Dict[str, Any]:
    """Monitor security events and generate alerts"""
    try:
        security_service = SecurityService(settings.secret_key)
        
        # Get recent security events
        recent_events = security_service.get_security_events(
            start_time=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        # Analyze events by severity
        high_severity_events = [
            event for event in recent_events 
            if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
        ]
        
        # Analyze events by type
        event_types = {}
        for event in recent_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        # Generate alerts for suspicious patterns
        alerts = []
        
        # Too many failed authentication attempts
        failed_auth_count = event_types.get("invalid_token", 0) + event_types.get("token_expired", 0)
        if failed_auth_count > 10:
            alerts.append({
                "type": "high_failed_auth",
                "severity": "high",
                "message": f"High number of failed authentication attempts: {failed_auth_count}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Too many rate limit violations
        rate_limit_violations = event_types.get("rate_limit_exceeded", 0)
        if rate_limit_violations > 50:
            alerts.append({
                "type": "high_rate_limit_violations",
                "severity": "medium",
                "message": f"High number of rate limit violations: {rate_limit_violations}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        # Suspicious IP activity
        ip_activity = {}
        for event in recent_events:
            ip_activity[event.ip_address] = ip_activity.get(event.ip_address, 0) + 1
        
        suspicious_ips = [
            ip for ip, count in ip_activity.items() 
            if count > 20 and ip != "0.0.0.0"
        ]
        
        for ip in suspicious_ips:
            alerts.append({
                "type": "suspicious_ip_activity",
                "severity": "high",
                "message": f"Suspicious activity from IP {ip}: {ip_activity[ip]} events",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip
            })
        
        result = {
            "total_events": len(recent_events),
            "high_severity_events": len(high_severity_events),
            "event_types": event_types,
            "alerts": alerts,
            "suspicious_ips": suspicious_ips,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Security monitoring completed: {len(alerts)} alerts generated")
        return result
        
    except Exception as e:
        logger.error(f"Error in security monitoring: {str(e)}")
        self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, name="security.cleanup_security_data")
def cleanup_security_data(self, days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean up old security data"""
    try:
        security_service = SecurityService(settings.secret_key)
        
        # Clean up old security events
        events_cleaned = security_service.cleanup_old_events(days_to_keep)
        
        # Clean up old rate limit data
        rate_limiter = RateLimiter()
        rate_limit_cleaned = rate_limiter.cleanup_old_data(days_to_keep * 24 * 3600)  # Convert to seconds
        
        result = {
            "events_cleaned": events_cleaned,
            "rate_limit_cleaned": rate_limit_cleaned,
            "days_to_keep": days_to_keep,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Security data cleanup completed: {events_cleaned} events, {rate_limit_cleaned} rate limit entries")
        return result
        
    except Exception as e:
        logger.error(f"Error in security data cleanup: {str(e)}")
        self.retry(countdown=300, max_retries=3)


@shared_task(bind=True, name="security.analyze_threat_patterns")
def analyze_threat_patterns(self) -> Dict[str, Any]:
    """Analyze threat patterns from security events"""
    try:
        security_service = SecurityService(settings.secret_key)
        
        # Get events from last 24 hours
        recent_events = security_service.get_security_events(
            start_time=datetime.utcnow() - timedelta(days=1)
        )
        
        # Analyze patterns
        patterns = {
            "brute_force_attempts": 0,
            "suspicious_ips": set(),
            "attack_types": {},
            "time_distribution": {},
            "resource_targets": {}
        }
        
        for event in recent_events:
            # Count brute force attempts
            if event.event_type in ["invalid_token", "failed_login"]:
                patterns["brute_force_attempts"] += 1
            
            # Track suspicious IPs
            if event.ip_address != "0.0.0.0":
                patterns["suspicious_ips"].add(event.ip_address)
            
            # Count attack types
            patterns["attack_types"][event.event_type] = patterns["attack_types"].get(event.event_type, 0) + 1
            
            # Time distribution (hourly)
            hour = event.timestamp.hour
            patterns["time_distribution"][hour] = patterns["time_distribution"].get(hour, 0) + 1
            
            # Resource targets
            if event.resource:
                patterns["resource_targets"][event.resource] = patterns["resource_targets"].get(event.resource, 0) + 1
        
        # Convert sets to lists for JSON serialization
        patterns["suspicious_ips"] = list(patterns["suspicious_ips"])
        
        # Identify peak attack hours
        peak_hours = sorted(
            patterns["time_distribution"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Identify most targeted resources
        top_targets = sorted(
            patterns["resource_targets"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        result = {
            "total_events": len(recent_events),
            "brute_force_attempts": patterns["brute_force_attempts"],
            "suspicious_ips_count": len(patterns["suspicious_ips"]),
            "suspicious_ips": patterns["suspicious_ips"],
            "attack_types": patterns["attack_types"],
            "peak_attack_hours": peak_hours,
            "top_targeted_resources": top_targets,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Threat pattern analysis completed: {len(patterns['suspicious_ips'])} suspicious IPs identified")
        return result
        
    except Exception as e:
        logger.error(f"Error in threat pattern analysis: {str(e)}")
        self.retry(countdown=300, max_retries=3)


@shared_task(bind=True, name="security.auto_block_suspicious_ips")
def auto_block_suspicious_ips(self, threshold: int = 50) -> Dict[str, Any]:
    """Automatically block IPs with suspicious activity"""
    try:
        security_service = SecurityService(settings.secret_key)
        
        # Get events from last hour
        recent_events = security_service.get_security_events(
            start_time=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        # Count events by IP
        ip_counts = {}
        for event in recent_events:
            if event.ip_address != "0.0.0.0":
                ip_counts[event.ip_address] = ip_counts.get(event.ip_address, 0) + 1
        
        # Find IPs exceeding threshold
        suspicious_ips = [
            ip for ip, count in ip_counts.items()
            if count >= threshold
        ]
        
        blocked_ips = []
        for ip in suspicious_ips:
            # Check if IP is already blocked
            if not security_service.is_ip_blocked(ip):
                security_service.block_ip(ip, duration_minutes=60)
                blocked_ips.append(ip)
        
        result = {
            "threshold": threshold,
            "suspicious_ips_found": len(suspicious_ips),
            "newly_blocked_ips": blocked_ips,
            "ip_activity_counts": ip_counts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if blocked_ips:
            logger.warning(f"Auto-blocked {len(blocked_ips)} suspicious IPs: {blocked_ips}")
        else:
            logger.info("No new IPs blocked in auto-block operation")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in auto-block operation: {str(e)}")
        self.retry(countdown=300, max_retries=3)


@shared_task(bind=True, name="security.generate_security_report")
def generate_security_report(self, report_type: str = "daily") -> Dict[str, Any]:
    """Generate security report"""
    try:
        security_service = SecurityService(settings.secret_key)
        
        # Determine time range based on report type
        if report_type == "daily":
            start_time = datetime.utcnow() - timedelta(days=1)
        elif report_type == "weekly":
            start_time = datetime.utcnow() - timedelta(weeks=1)
        elif report_type == "monthly":
            start_time = datetime.utcnow() - timedelta(days=30)
        else:
            start_time = datetime.utcnow() - timedelta(days=1)
        
        # Get events for the period
        events = security_service.get_security_events(start_time=start_time)
        
        # Generate statistics
        stats = security_service.get_security_stats()
        
        # Analyze by severity
        severity_counts = {}
        for event in events:
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Analyze by type
        type_counts = {}
        for event in events:
            event_type = event.event_type
            type_counts[event_type] = type_counts.get(event_type, 0) + 1
        
        # Top IPs by activity
        ip_activity = {}
        for event in events:
            if event.ip_address != "0.0.0.0":
                ip_activity[event.ip_address] = ip_activity.get(event.ip_address, 0) + 1
        
        top_ips = sorted(ip_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Generate recommendations
        recommendations = []
        
        if severity_counts.get("high", 0) > 10:
            recommendations.append("High number of high-severity events detected. Review security policies.")
        
        if severity_counts.get("critical", 0) > 0:
            recommendations.append("Critical security events detected. Immediate action required.")
        
        if len(ip_activity) > 100:
            recommendations.append("High number of unique IPs. Consider implementing stricter rate limiting.")
        
        if type_counts.get("invalid_token", 0) > 20:
            recommendations.append("High number of invalid tokens. Review authentication system.")
        
        report = {
            "report_type": report_type,
            "period": {
                "start": start_time.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_events": len(events),
                "unique_ips": len(ip_activity),
                "blocked_ips": len(security_service.blocked_ips)
            },
            "severity_distribution": severity_counts,
            "event_type_distribution": type_counts,
            "top_active_ips": top_ips,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Security report generated: {report_type} report with {len(events)} events")
        return report
        
    except Exception as e:
        logger.error(f"Error generating security report: {str(e)}")
        self.retry(countdown=300, max_retries=3)


@shared_task(bind=True, name="security.validate_input_batch")
def validate_input_batch(self, inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate a batch of inputs"""
    try:
        validator = InputValidator()
        
        results = []
        valid_count = 0
        invalid_count = 0
        
        for input_data in inputs:
            input_type = input_data.get("type", "general")
            value = input_data.get("value", "")
            level = input_data.get("level", "normal")
            
            # Convert level string to enum
            if level == "strict":
                validation_level = validator.ValidationLevel.STRICT
            elif level == "lenient":
                validation_level = validator.ValidationLevel.LENIENT
            else:
                validation_level = validator.ValidationLevel.NORMAL
            
            # Validate input
            if input_type == "url":
                result = validator.validate_url(value, validation_level)
            elif input_type == "email":
                result = validator.validate_email(value)
            elif input_type == "filename":
                result = validator.validate_filename(value)
            else:
                result = validator.validate_and_sanitize_input(value, input_type, validation_level)
            
            results.append({
                "input": input_data,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "sanitized_value": result.sanitized_value
            })
            
            if result.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        result = {
            "total_inputs": len(inputs),
            "valid_inputs": valid_count,
            "invalid_inputs": invalid_count,
            "validation_rate": valid_count / len(inputs) if inputs else 0,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Input validation batch completed: {valid_count}/{len(inputs)} valid")
        return result
        
    except Exception as e:
        logger.error(f"Error in input validation batch: {str(e)}")
        self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, name="security.health_check")
def security_health_check(self) -> Dict[str, Any]:
    """Perform security system health check"""
    try:
        security_service = SecurityService(settings.secret_key)
        rate_limiter = RateLimiter()
        validator = InputValidator()
        
        # Test security service
        test_token = security_service.generate_token("test_user", expires_in=60)
        token_payload = security_service.verify_token(test_token)
        
        # Test rate limiter
        test_identifier = "test_rate_limit"
        rate_limit_result = rate_limiter.check_limit("test", test_identifier)
        
        # Test validator
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        validation_result = validator.validate_url(test_url)
        
        # Check system status
        health_status = {
            "security_service": {
                "status": "healthy" if token_payload else "unhealthy",
                "token_generation": bool(test_token),
                "token_verification": bool(token_payload)
            },
            "rate_limiter": {
                "status": "healthy" if rate_limit_result.allowed else "unhealthy",
                "rate_limit_check": rate_limit_result.allowed
            },
            "input_validator": {
                "status": "healthy" if validation_result.is_valid else "unhealthy",
                "url_validation": validation_result.is_valid
            },
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Determine overall status
        if not all([
            health_status["security_service"]["status"] == "healthy",
            health_status["rate_limiter"]["status"] == "healthy",
            health_status["input_validator"]["status"] == "healthy"
        ]):
            health_status["overall_status"] = "unhealthy"
        
        logger.info(f"Security health check completed: {health_status['overall_status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Error in security health check: {str(e)}")
        return {
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 