from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import hashlib
import secrets
import jwt

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


def hash_password(password: str) -> tuple[str, str]:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify password against hash"""
    return hashlib.sha256((password + salt).encode()).hexdigest() == hashed_password


def generate_token(user_id: str, expires_in: int = 3600) -> str:
    """Generate JWT token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
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
    # Basic validation
    if len(request.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters long"
        )
    
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    
    # Check if username already exists
    if user_repo.get_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    
    # Check if email already exists
    if user_repo.get_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
    
    # Hash password
    hashed_password, salt = hash_password(request.password)
    
    # Create user
    user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password,
        salt=salt,
        role=UserRole.USER
    )
    
    created_user = user_repo.create(user)
    
    return UserResponse(
        id=str(created_user.id),
        username=created_user.username,
        email=created_user.email,
        full_name=created_user.full_name,
        role=created_user.role.value,
        is_active=created_user.is_active,
        created_at=created_user.created_at,
        updated_at=created_user.updated_at
    )


@router.post("/login", response_model=Dict[str, Any])
async def login_user(request: UserLoginRequest, req: Request, db: Session = Depends(get_db)):
    """Login user"""
    user_repo = SQLAlchemyUserRepository(db)
    
    # Try to find user by username or email
    user = user_repo.get_by_username(request.username_or_email)
    if not user:
        user = user_repo.get_by_email(request.username_or_email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    if not verify_password(request.password, user.hashed_password, user.salt):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate token
    token = generate_token(str(user.id), expires_in=request.expires_in or 3600)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": request.expires_in or 3600,
        "user": UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    }


@router.post("/logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user), req: Request = None):
    """Logout user"""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    request: UserProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(current_user["id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if request.username:
        existing_user = user_repo.get_by_username(request.username)
        if existing_user and str(existing_user.id) != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        user.username = request.username
    
    if request.email:
        existing_user = user_repo.get_by_email(request.email)
        if existing_user and str(existing_user.id) != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        user.email = request.email
    
    user.updated_at = datetime.utcnow()
    updated_user = user_repo.update(user)
    
    return UserProfileResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role.value,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
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
    
    if not verify_password(request.current_password, user.hashed_password, user.salt):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    hashed_password, salt = hash_password(request.new_password)
    user.hashed_password = hashed_password
    user.salt = salt
    user.updated_at = datetime.utcnow()
    
    user_repo.update(user)
    
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
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    users, total = user_repo.get_all(page=page, size=size, search=search)
    
    return UserListResponse(
        users=[
            UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            ) for user in users
        ],
        total=total,
        page=page,
        size=size
    )


@router.get("/users/stats", response_model=UserStatsResponse)
async def get_user_stats(current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user statistics (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    stats = user_repo.get_stats()
    
    return UserStatsResponse(**stats)


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only)"""
    if current_user["role"] != "admin":
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
    
    user.is_active = not user.is_active
    user.updated_at = datetime.utcnow()
    updated_user = user_repo.update(user)
    
    return {
        "message": f"User {'activated' if updated_user.is_active else 'deactivated'} successfully",
        "user": UserResponse(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email,
            role=updated_user.role.value,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
    }


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make user admin (admin only)"""
    if current_user["role"] != "admin":
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
    
    user.role = UserRole.ADMIN
    user.updated_at = datetime.utcnow()
    updated_user = user_repo.update(user)
    
    return {
        "message": "User promoted to admin successfully",
        "user": UserResponse(
            id=str(updated_user.id),
            username=updated_user.username,
            email=updated_user.email,
            role=updated_user.role.value,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if str(current_user["id"]) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_repo.delete(user_id)
    
    return {"message": "User deleted successfully"}


def create_default_admin():
    """Create default admin user"""
    try:
        db = next(get_db())
        user_repo = SQLAlchemyUserRepository(db)
        
        # Check if admin already exists
        admin = user_repo.get_by_username("admin")
        if admin:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        hashed_password, salt = hash_password("admin123")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            salt=salt,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        user_repo.create(admin_user)
        logger.info("Default admin user created successfully")
        
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")
    finally:
        db.close() 