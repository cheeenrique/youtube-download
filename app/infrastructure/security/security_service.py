import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import re
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    event_type: str
    severity: SecurityLevel
    user_id: Optional[str]
    ip_address: str
    timestamp: datetime
    details: Dict[str, Any]
    resource: Optional[str] = None


class SecurityService:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.security_events: List[SecurityEvent] = []
        self.rate_limit_store: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        
    def generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token for user authentication"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            self._log_security_event("token_expired", SecurityLevel.MEDIUM, None, "0.0.0.0")
            return None
        except jwt.InvalidTokenError:
            self._log_security_event("invalid_token", SecurityLevel.MEDIUM, None, "0.0.0.0")
            return None
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            return hmac.compare_digest(key.decode(), hashed_password)
        except Exception:
            return False
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def validate_input(self, data: str, input_type: str = "general") -> Tuple[bool, str]:
        """Validate and sanitize input data"""
        if not data or len(data.strip()) == 0:
            return False, "Input cannot be empty"
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', data.strip())
        
        if input_type == "url":
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(sanitized):
                return False, "Invalid URL format"
        
        elif input_type == "email":
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(sanitized):
                return False, "Invalid email format"
        
        elif input_type == "filename":
            # Prevent path traversal and dangerous characters
            dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            if any(char in sanitized for char in dangerous_chars):
                return False, "Filename contains invalid characters"
        
        return True, sanitized
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100, window: int = 3600) -> bool:
        """Check rate limiting for identifier (IP, user, etc.)"""
        current_time = time.time()
        
        if identifier not in self.rate_limit_store:
            self.rate_limit_store[identifier] = []
        
        # Remove old requests outside the window
        self.rate_limit_store[identifier] = [
            req_time for req_time in self.rate_limit_store[identifier]
            if current_time - req_time < window
        ]
        
        # Check if limit exceeded
        if len(self.rate_limit_store[identifier]) >= max_requests:
            return False
        
        # Add current request
        self.rate_limit_store[identifier].append(current_time)
        return True
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        if ip_address in self.blocked_ips:
            if datetime.utcnow() < self.blocked_ips[ip_address]:
                return True
            else:
                del self.blocked_ips[ip_address]
        return False
    
    def block_ip(self, ip_address: str, duration_minutes: int = 60) -> None:
        """Block IP address for specified duration"""
        self.blocked_ips[ip_address] = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self._log_security_event("ip_blocked", SecurityLevel.HIGH, None, ip_address, 
                               {"duration_minutes": duration_minutes})
    
    def unblock_ip(self, ip_address: str) -> None:
        """Unblock IP address"""
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]
            self._log_security_event("ip_unblocked", SecurityLevel.MEDIUM, None, ip_address)
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """Generate secure filename to prevent path traversal"""
        # Remove dangerous characters and extensions
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', original_filename)
        safe_name = re.sub(r'\.(exe|bat|cmd|com|pif|scr|vbs|js)$', '.txt', safe_name, flags=re.IGNORECASE)
        
        # Add timestamp for uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{safe_name}"
    
    def validate_file_upload(self, filename: str, file_size: int, max_size: int = 100 * 1024 * 1024) -> Tuple[bool, str]:
        """Validate file upload security"""
        # Check file size
        if file_size > max_size:
            return False, f"File size exceeds maximum allowed size of {max_size} bytes"
        
        # Check file extension
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js']
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in dangerous_extensions:
            return False, "File type not allowed"
        
        # Validate filename
        is_valid, sanitized_name = self.validate_input(filename, "filename")
        if not is_valid:
            return False, sanitized_name
        
        return True, "File upload validated"
    
    def _log_security_event(self, event_type: str, severity: Union[SecurityLevel, str], user_id: Optional[str], 
                           ip_address: str, details: Optional[Dict[str, Any]] = None, 
                           resource: Optional[str] = None) -> None:
        """Log security event"""
        # Convert string to SecurityLevel if needed
        if isinstance(severity, str):
            try:
                severity = SecurityLevel(severity)
            except ValueError:
                severity = SecurityLevel.LOW  # Default to LOW if invalid
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            details=details or {},
            resource=resource
        )
        self.security_events.append(event)
        
        # Log to system logger
        log_message = f"Security Event: {event_type} | Severity: {severity.value} | IP: {ip_address}"
        if user_id:
            log_message += f" | User: {user_id}"
        if resource:
            log_message += f" | Resource: {resource}"
        
        if severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_security_events(self, severity: Optional[SecurityLevel] = None, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> List[SecurityEvent]:
        """Get security events with optional filtering"""
        events = self.security_events
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        return events
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        total_events = len(self.security_events)
        events_by_severity = {}
        events_by_type = {}
        
        for event in self.security_events:
            # Count by severity
            severity = event.severity.value
            events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
            
            # Count by type
            event_type = event.event_type
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        return {
            "total_events": total_events,
            "events_by_severity": events_by_severity,
            "events_by_type": events_by_type,
            "blocked_ips_count": len(self.blocked_ips),
            "rate_limited_identifiers": len(self.rate_limit_store)
        }
    
    def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """Clean up old security events"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        original_count = len(self.security_events)
        
        self.security_events = [
            event for event in self.security_events
            if event.timestamp > cutoff_date
        ]
        
        removed_count = original_count - len(self.security_events)
        logger.info(f"Cleaned up {removed_count} old security events")
        return removed_count 