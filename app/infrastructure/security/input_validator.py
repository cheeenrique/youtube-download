import re
import mimetypes
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"


@dataclass
class ValidationRule:
    name: str
    pattern: str
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_extensions: Optional[List[str]] = None
    max_size: Optional[int] = None
    required: bool = True


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Optional[str] = None


class InputValidator:
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules"""
        # URL validation
        self.rules["url"] = ValidationRule(
            name="url",
            pattern=r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$',
            min_length=10,
            max_length=2048
        )
        
        # Email validation
        self.rules["email"] = ValidationRule(
            name="email",
            pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            min_length=5,
            max_length=254
        )
        
        # Filename validation
        self.rules["filename"] = ValidationRule(
            name="filename",
            pattern=r'^[a-zA-Z0-9._-]+$',
            min_length=1,
            max_length=255,
            allowed_extensions=[".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"]
        )
        
        # Username validation
        self.rules["username"] = ValidationRule(
            name="username",
            pattern=r'^[a-zA-Z0-9_-]+$',
            min_length=3,
            max_length=50
        )
        
        # Password validation
        self.rules["password"] = ValidationRule(
            name="password",
            pattern=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
            min_length=8,
            max_length=128
        )
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a custom validation rule"""
        self.rules[rule.name] = rule
    
    def validate_url(self, url: str, level: ValidationLevel = ValidationLevel.NORMAL) -> ValidationResult:
        """Validate URL with different levels of strictness"""
        errors = []
        warnings = []
        sanitized_value = url.strip()
        
        if not sanitized_value:
            return ValidationResult(False, ["URL cannot be empty"], [], None)
        
        # Basic URL pattern validation
        url_pattern = re.compile(self.rules["url"].pattern, re.IGNORECASE)
        if not url_pattern.match(sanitized_value):
            errors.append("Invalid URL format")
        
        # Length validation
        if len(sanitized_value) < self.rules["url"].min_length:
            errors.append(f"URL too short (minimum {self.rules['url'].min_length} characters)")
        
        if len(sanitized_value) > self.rules["url"].max_length:
            errors.append(f"URL too long (maximum {self.rules['url'].max_length} characters)")
        
        # Protocol validation
        if not sanitized_value.startswith(('http://', 'https://')):
            errors.append("URL must start with http:// or https://")
        
        # Domain validation for strict level
        if level == ValidationLevel.STRICT:
            domain_pattern = re.compile(r'^https?://([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}')
            if not domain_pattern.match(sanitized_value):
                errors.append("Invalid domain format")
        
        # Security checks
        dangerous_patterns = [
            r'javascript:', r'data:', r'vbscript:', r'file:', r'ftp:'
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized_value, re.IGNORECASE):
                errors.append(f"URL contains dangerous protocol: {pattern}")
        
        # YouTube URL specific validation
        if 'youtube.com' in sanitized_value or 'youtu.be' in sanitized_value:
            if not self._is_valid_youtube_url(sanitized_value):
                errors.append("Invalid YouTube URL format")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_value if len(errors) == 0 else None
        )
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """Validate YouTube URL format"""
        youtube_patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url):
                return True
        return False
    
    def validate_email(self, email: str) -> ValidationResult:
        """Validate email address"""
        errors = []
        warnings = []
        sanitized_value = email.strip().lower()
        
        if not sanitized_value:
            return ValidationResult(False, ["Email cannot be empty"], [], None)
        
        # Pattern validation
        email_pattern = re.compile(self.rules["email"].pattern)
        if not email_pattern.match(sanitized_value):
            errors.append("Invalid email format")
        
        # Length validation
        if len(sanitized_value) < self.rules["email"].min_length:
            errors.append(f"Email too short (minimum {self.rules['email'].min_length} characters)")
        
        if len(sanitized_value) > self.rules["email"].max_length:
            errors.append(f"Email too long (maximum {self.rules['email'].max_length} characters)")
        
        # Additional checks
        if sanitized_value.count('@') != 1:
            errors.append("Email must contain exactly one @ symbol")
        
        local_part, domain = sanitized_value.split('@', 1)
        if len(local_part) == 0 or len(domain) == 0:
            errors.append("Invalid email format")
        
        if domain.count('.') == 0:
            errors.append("Domain must contain at least one dot")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_value if len(errors) == 0 else None
        )
    
    def validate_filename(self, filename: str, allowed_extensions: Optional[List[str]] = None) -> ValidationResult:
        """Validate filename"""
        errors = []
        warnings = []
        sanitized_value = filename.strip()
        
        if not sanitized_value:
            return ValidationResult(False, ["Filename cannot be empty"], [], None)
        
        # Length validation
        if len(sanitized_value) < self.rules["filename"].min_length:
            errors.append(f"Filename too short (minimum {self.rules['filename'].min_length} characters)")
        
        if len(sanitized_value) > self.rules["filename"].max_length:
            errors.append(f"Filename too long (maximum {self.rules['filename'].max_length} characters)")
        
        # Pattern validation
        filename_pattern = re.compile(self.rules["filename"].pattern)
        if not filename_pattern.match(sanitized_value):
            errors.append("Filename contains invalid characters")
        
        # Dangerous characters check
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in sanitized_value:
                errors.append(f"Filename contains dangerous character: {char}")
        
        # Extension validation
        if allowed_extensions:
            file_ext = self._get_file_extension(sanitized_value)
            if file_ext and file_ext.lower() not in [ext.lower() for ext in allowed_extensions]:
                errors.append(f"File extension not allowed: {file_ext}")
        else:
            # Use default allowed extensions
            file_ext = self._get_file_extension(sanitized_value)
            if file_ext and file_ext.lower() not in [ext.lower() for ext in self.rules["filename"].allowed_extensions]:
                warnings.append(f"File extension may not be supported: {file_ext}")
        
        # Reserved names check
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if sanitized_value.upper() in reserved_names:
            errors.append("Filename is a reserved system name")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_value if len(errors) == 0 else None
        )
    
    def _get_file_extension(self, filename: str) -> Optional[str]:
        """Extract file extension from filename"""
        if '.' in filename:
            return '.' + filename.split('.')[-1]
        return None
    
    def validate_file_upload(self, filename: str, file_size: int, content_type: Optional[str] = None,
                           max_size: Optional[int] = None) -> ValidationResult:
        """Validate file upload"""
        errors = []
        warnings = []
        
        # Validate filename
        filename_result = self.validate_filename(filename)
        if not filename_result.is_valid:
            errors.extend(filename_result.errors)
        else:
            warnings.extend(filename_result.warnings)
        
        # Size validation
        max_allowed_size = max_size or (100 * 1024 * 1024)  # 100MB default
        if file_size > max_allowed_size:
            errors.append(f"File size ({file_size} bytes) exceeds maximum allowed size ({max_allowed_size} bytes)")
        
        # Content type validation
        if content_type:
            allowed_mime_types = [
                'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo',
                'video/x-matroska', 'video/webm', 'video/x-flv', 'video/x-ms-wmv',
                'video/x-m4v', 'video/3gpp', 'video/ogg'
            ]
            
            if content_type not in allowed_mime_types:
                warnings.append(f"Content type '{content_type}' may not be supported")
        
        # Extension vs content type mismatch check
        if content_type and filename_result.sanitized_value:
            file_ext = self._get_file_extension(filename_result.sanitized_value)
            if file_ext:
                expected_mime = mimetypes.guess_type(filename_result.sanitized_value)[0]
                if expected_mime and expected_mime != content_type:
                    warnings.append(f"Content type '{content_type}' doesn't match file extension '{file_ext}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=filename_result.sanitized_value if filename_result.is_valid else None
        )
    
    def validate_json_data(self, data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
        """Validate JSON data against a schema"""
        errors = []
        warnings = []
        
        for field_name, field_config in schema.items():
            field_value = data.get(field_name)
            
            # Required field check
            if field_config.get('required', False) and field_value is None:
                errors.append(f"Required field '{field_name}' is missing")
                continue
            
            # Skip validation if field is not present and not required
            if field_value is None:
                continue
            
            # Type validation
            expected_type = field_config.get('type')
            if expected_type and not isinstance(field_value, expected_type):
                errors.append(f"Field '{field_name}' must be of type {expected_type.__name__}")
                continue
            
            # String-specific validations
            if isinstance(field_value, str):
                # Length validation
                min_length = field_config.get('min_length')
                max_length = field_config.get('max_length')
                
                if min_length and len(field_value) < min_length:
                    errors.append(f"Field '{field_name}' too short (minimum {min_length} characters)")
                
                if max_length and len(field_value) > max_length:
                    errors.append(f"Field '{field_name}' too long (maximum {max_length} characters)")
                
                # Pattern validation
                pattern = field_config.get('pattern')
                if pattern and not re.match(pattern, field_value):
                    errors.append(f"Field '{field_name}' doesn't match required pattern")
            
            # Number-specific validations
            elif isinstance(field_value, (int, float)):
                min_value = field_config.get('min_value')
                max_value = field_config.get('max_value')
                
                if min_value is not None and field_value < min_value:
                    errors.append(f"Field '{field_name}' too small (minimum {min_value})")
                
                if max_value is not None and field_value > max_value:
                    errors.append(f"Field '{field_name}' too large (maximum {max_value})")
            
            # List-specific validations
            elif isinstance(field_value, list):
                min_items = field_config.get('min_items')
                max_items = field_config.get('max_items')
                
                if min_items and len(field_value) < min_items:
                    errors.append(f"Field '{field_name}' too few items (minimum {min_items})")
                
                if max_items and len(field_value) > max_items:
                    errors.append(f"Field '{field_name}' too many items (maximum {max_items})")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=data if len(errors) == 0 else None
        )
    
    def sanitize_html(self, html_content: str) -> str:
        """Basic HTML sanitization"""
        # Remove script tags and their content
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove other dangerous tags
        dangerous_tags = ['iframe', 'object', 'embed', 'form', 'input', 'textarea', 'select']
        for tag in dangerous_tags:
            html_content = re.sub(rf'<{tag}[^>]*>.*?</{tag}>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
            html_content = re.sub(rf'<{tag}[^>]*/?>', '', html_content, flags=re.IGNORECASE)
        
        # Remove dangerous attributes
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur']
        for attr in dangerous_attrs:
            html_content = re.sub(rf'{attr}="[^"]*"', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(rf"{attr}='[^']*'", '', html_content, flags=re.IGNORECASE)
        
        return html_content
    
    def validate_and_sanitize_input(self, input_data: str, input_type: str = "general",
                                  level: ValidationLevel = ValidationLevel.NORMAL) -> ValidationResult:
        """Generic input validation and sanitization"""
        errors = []
        warnings = []
        sanitized_value = input_data.strip()
        
        if not sanitized_value:
            return ValidationResult(False, ["Input cannot be empty"], [], None)
        
        # Remove null bytes and control characters
        sanitized_value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized_value)
        
        # Type-specific validation
        if input_type == "url":
            return self.validate_url(sanitized_value, level)
        elif input_type == "email":
            return self.validate_email(sanitized_value)
        elif input_type == "filename":
            return self.validate_filename(sanitized_value)
        elif input_type == "html":
            sanitized_value = self.sanitize_html(sanitized_value)
            warnings.append("HTML content has been sanitized")
        
        # General length validation
        if len(sanitized_value) > 10000:  # 10KB limit for general input
            errors.append("Input too long (maximum 10KB)")
        
        # Check for potential SQL injection patterns
        sql_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\b(OR|AND)\s+\'[^\']*\'\s*=\s*\'[^\']*\')',
            r'(\b(OR|AND)\s+\"[^\"]*\"\s*=\s*\"[^\"]*\")'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, sanitized_value, re.IGNORECASE):
                warnings.append("Input contains potential SQL injection patterns")
                break
        
        # Check for potential XSS patterns
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, sanitized_value, re.IGNORECASE):
                warnings.append("Input contains potential XSS patterns")
                break
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized_value if len(errors) == 0 else None
        ) 