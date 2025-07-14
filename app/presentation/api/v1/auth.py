from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import hashlib
import secrets

from app.infrastructure.security.security_service import SecurityService, SecurityLevel
from app.infrastructure.security.input_validator import InputValidator
from app.presentation.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, UserResponse, 
    PasswordChangeRequest, UserProfileRequest, UserProfileResponse,
    UserListResponse, UserStatsResponse
)
from app.shared.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories.user_repository_impl import SQLAlchemyUserRepository
from app.domain.entities.user import User, UserRole
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Initialize services
# settings já importado globalmente
security_service = SecurityService(settings.secret_key)
input_validator = InputValidator()

# Remover users_db e user_sessions


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = security_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user.to_dict()


@router.post("/register", response_model=UserResponse)
async def register_user(request: UserRegisterRequest, req: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    # Validate input
    username_validation = input_validator.validate_and_sanitize_input(
        request.username, "username"
    )
    if not username_validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid username: {', '.join(username_validation.errors)}"
        )
    
    email_validation = input_validator.validate_email(request.email)
    if not email_validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email: {', '.join(email_validation.errors)}"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    
    # Check if username already exists
    if user_repo.get_by_username(username_validation.sanitized_value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Check if email already exists
    if user_repo.get_by_email(email_validation.sanitized_value):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    
    # Hash password
    hashed_password, salt = security_service.hash_password(request.password)
    
    # Create user entity
    user = User(
        username=username_validation.sanitized_value,
        email=email_validation.sanitized_value,
        hashed_password=hashed_password,
        salt=salt,
        full_name=request.full_name,
        role=UserRole.USER,
        is_active=True,
        preferences=request.preferences or {}
    )
    
    # Save user
    user = user_repo.create(user)
    
    # Log security event
    security_service._log_security_event(
        "user_registered", SecurityLevel.LOW.value, 
        str(user.id), req.client.host, {"username": user.username}
    )
    
    logger.info(f"New user registered: {user.username}")
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        last_login=user.last_login,
        login_count=0
    )


@router.post("/login", response_model=Dict[str, Any])
async def login_user(request: UserLoginRequest, req: Request, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user_repo = SQLAlchemyUserRepository(db)
    
    # Find user by username or email
    user = user_repo.get_by_username(request.username)
    if not user:
        user = user_repo.get_by_email(request.username)
    
    if not user:
        security_service._log_security_event(
            "login_failed", SecurityLevel.MEDIUM.value, 
            None, req.client.host, {"username": request.username, "reason": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
    
    if not user.can_login():
        security_service._log_security_event(
            "login_failed", SecurityLevel.MEDIUM.value, 
            str(user.id), req.client.host, {"username": user.username, "reason": "account_disabled_or_locked"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled or locked"
        )
    
    # Verify password
    if not security_service.verify_password(request.password, user.hashed_password, user.salt):
        # Increment login attempts
        user.increment_login_attempts()
        user_repo.update(user)
        
        # Lock account if too many attempts
        if user.login_attempts >= 5:
            user.lock_account()
            user_repo.update(user)
        
        security_service._log_security_event(
            "login_failed", SecurityLevel.MEDIUM.value, 
            str(user.id), req.client.host, {"username": user.username, "reason": "invalid_password"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
    
    # Reset login attempts and update last login
    user.reset_login_attempts()
    user.update_last_login()
    user_repo.update(user)
    
    # Generate token
    token = security_service.generate_token(str(user.id), expires_in=request.expires_in or 3600)
    
    # Log successful login
    security_service._log_security_event(
        "login_successful", SecurityLevel.LOW.value, 
        str(user.id), req.client.host, {"username": user.username}
    )
    
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": request.expires_in or 3600,
        "user": UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login=user.last_login,
            login_count=0  # TODO: Implement login count
        )
    }


@router.post("/logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user), req: Request = None):
    """Logout user (invalidate session)"""
    # In a real application, you might want to blacklist the token
    # For now, we'll just log the logout event
    
    security_service._log_security_event(
        "logout", SecurityLevel.LOW.value, 
        current_user["id"], req.client.host if req else "0.0.0.0", 
        {"username": current_user["username"]}
    )
    
    logger.info(f"User logged out: {current_user['username']}")
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        is_active=current_user["is_active"],
        is_admin=current_user["is_admin"],
        created_at=current_user["created_at"],
        last_login=current_user["last_login"],
        login_count=current_user["login_count"]
    )


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    request: UserProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update current user profile"""
    db: Session = Depends(get_db)
    # Validate email if provided
    if request.email and request.email != current_user["email"]:
        email_validation = input_validator.validate_email(request.email)
        if not email_validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid email: {', '.join(email_validation.errors)}"
            )
        
        # Check if email already exists
        if db.query(UserModel).filter(UserModel.email == email_validation.sanitized_value).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        
        current_user["email"] = email_validation.sanitized_value
    
    # Update other fields
    if request.full_name is not None:
        current_user["full_name"] = request.full_name
    
    if request.preferences is not None:
        current_user["preferences"].update(request.preferences)
    
    logger.info(f"User profile updated: {current_user['username']}")
    
    return UserProfileResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        preferences=current_user["preferences"],
        updated_at=datetime.utcnow()
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not security_service.verify_password(request.current_password, user.hashed_password, user.salt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Hash new password
    hashed_password, salt = security_service.hash_password(request.new_password)
    
    # Update password
    user.change_password(hashed_password, salt)
    user_repo.update(user)
    
    logger.info(f"Password changed for user: {user.username}")
    
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List users (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    
    # Get users with search
    if search:
        users = user_repo.search_users(search, skip=(page - 1) * size, limit=size)
        total = len(user_repo.search_users(search))  # Get total count
    else:
        users = user_repo.get_all(skip=(page - 1) * size, limit=size)
        total = user_repo.count_users()
    
    return UserListResponse(
        users=[
            UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login=user.last_login,
                login_count=0  # TODO: Implement login count
            )
            for user in users
        ],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/users/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user statistics (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    stats = user_repo.get_user_stats()
    
    return UserStatsResponse(
        total_users=stats['total_users'],
        active_users=stats['active_users'],
        admin_users=stats['admin_users'],
        recent_registrations=stats['recent_registrations'],
        recent_logins=stats['recent_logins'],
        registration_rate=stats['registration_rate'],
        login_rate=stats['login_rate']
    )


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_active:
        user.deactivate()
    else:
        user.activate()
    
    user_repo.update(user)
    
    status_text = "activated" if user.is_active else "deactivated"
    logger.info(f"User {user.username} {status_text} by admin {current_user['username']}")
    
    return {
        "message": f"User {status_text} successfully",
        "user_id": user_id,
        "is_active": user.is_active
    }


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make user admin (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.promote_to_admin()
    user_repo.update(user)
    
    logger.info(f"User {user.username} made admin by {current_user['username']}")
    
    return {
        "message": "User made admin successfully",
        "user_id": user_id,
        "is_admin": True
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    username = user.username
    user_repo.delete(user_id)
    
    logger.info(f"User {username} deleted by admin {current_user['username']}")
    
    return {"message": "User deleted successfully"}


# Create default admin user on startup
def create_default_admin():
    """Create default admin user if no users exist"""
    db: Session = Depends(get_db)
    if db.query(UserModel).count() == 0:
        hashed_password, salt = security_service.hash_password("admin123")
        admin_user = UserModel(
            id="admin_default",
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            salt=salt,
            full_name="System Administrator",
            is_active=True,
            is_admin=True,
            created_at=datetime.utcnow(),
            last_login=None,
            login_count=0,
            preferences={}
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info("Default admin user created: admin/admin123")


# Create default admin on module import
# create_default_admin()  # Removed to avoid Depends error on module import 