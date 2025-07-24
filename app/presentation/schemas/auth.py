from pydantic import BaseModel, Field, EmailStr, validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username for the account")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class UserLoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    expires_in: Optional[int] = Field(3600, ge=300, le=86400, description="Token expiration time in seconds")


class UserResponse(BaseModel):
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account update timestamp")


class UserProfileRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username")
    email: Optional[EmailStr] = Field(None, description="New email address")
    full_name: Optional[str] = Field(None, max_length=100, description="New full name")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Updated preferences")


class UserProfileResponse(BaseModel):
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account update timestamp")


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserListResponse(BaseModel):
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class UserStatsResponse(BaseModel):
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    admin_users: int = Field(..., description="Number of admin users")
    recent_registrations: int = Field(..., description="Registrations in last 30 days")
    recent_logins: int = Field(..., description="Logins in last 7 days")
    registration_rate: float = Field(..., description="Average registrations per day")
    login_rate: float = Field(..., description="Average logins per day")


class AuthStatusResponse(BaseModel):
    is_authenticated: bool = Field(..., description="Whether user is authenticated")
    user: Optional[UserResponse] = Field(None, description="User information if authenticated")
    token_expires_at: Optional[datetime] = Field(None, description="Token expiration time")


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address for password reset")


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserSessionResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Session creation timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    ip_address: str = Field(..., description="IP address of the session")
    user_agent: str = Field(..., description="User agent string")


class UserActivityResponse(BaseModel):
    activity_id: str = Field(..., description="Activity ID")
    user_id: str = Field(..., description="User ID")
    activity_type: str = Field(..., description="Type of activity")
    description: str = Field(..., description="Activity description")
    timestamp: datetime = Field(..., description="Activity timestamp")
    ip_address: str = Field(..., description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UserPreferencesRequest(BaseModel):
    theme: Optional[str] = Field(None, description="UI theme preference")
    language: Optional[str] = Field(None, description="Language preference")
    timezone: Optional[str] = Field(None, description="Timezone preference")
    notifications: Optional[Dict[str, bool]] = Field(None, description="Notification preferences")
    download_settings: Optional[Dict[str, Any]] = Field(None, description="Download preferences")


class UserPreferencesResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AdminUserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    is_admin: bool = Field(False, description="Whether the user should be an admin")
    is_active: bool = Field(True, description="Whether the user should be active")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class AdminUserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = Field(None, description="New email address")
    full_name: Optional[str] = Field(None, max_length=100, description="New full name")
    is_admin: Optional[bool] = Field(None, description="Admin status")
    is_active: Optional[bool] = Field(None, description="Active status")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class UserSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class UserSearchResponse(BaseModel):
    users: List[UserResponse] = Field(..., description="Matching users")
    total: int = Field(..., description="Total number of matches")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
    query: str = Field(..., description="Search query used")


class UserBulkActionRequest(BaseModel):
    user_ids: List[str] = Field(..., description="List of user IDs")
    action: str = Field(..., description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")


class UserBulkActionResponse(BaseModel):
    action: str = Field(..., description="Action performed")
    affected_users: int = Field(..., description="Number of users affected")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(None, description="List of errors")


class UserExportRequest(BaseModel):
    format: str = Field("json", description="Export format (json, csv, xlsx)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Export filters")
    fields: Optional[List[str]] = Field(None, description="Fields to include")


class UserExportResponse(BaseModel):
    export_id: str = Field(..., description="Export ID")
    format: str = Field(..., description="Export format")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    created_at: datetime = Field(..., description="Export creation timestamp")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class UserImportRequest(BaseModel):
    file_url: str = Field(..., description="URL of the import file")
    format: str = Field("csv", description="Import format (csv, xlsx)")
    options: Optional[Dict[str, Any]] = Field(None, description="Import options")


class UserImportResponse(BaseModel):
    import_id: str = Field(..., description="Import ID")
    status: str = Field(..., description="Import status")
    total_records: int = Field(..., description="Total records to import")
    processed_records: int = Field(..., description="Records processed so far")
    success_count: int = Field(..., description="Successfully imported records")
    error_count: int = Field(..., description="Failed records")
    errors: List[Dict[str, Any]] = Field(..., description="List of import errors")
    created_at: datetime = Field(..., description="Import creation timestamp")


class UserAuditLogRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    start_date: Optional[datetime] = Field(None, description="Start date for audit log")
    end_date: Optional[datetime] = Field(None, description="End date for audit log")
    activity_types: Optional[List[str]] = Field(None, description="Filter by activity types")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Page size")


class UserAuditLogResponse(BaseModel):
    activities: List[UserActivityResponse] = Field(..., description="List of activities")
    total: int = Field(..., description="Total number of activities")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
    user_id: str = Field(..., description="User ID") 