"""Authentication API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ...config import settings
from ...models.schema import User, UserSettings
from ..auth import (
    hash_password,
    needs_rehash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from ..deps import get_db_session, get_current_user, get_admin_user
from ..errors import ErrorCode, raise_api_error
from ..schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    PasswordChange,
    PasswordReset,
    UserResponse,
    UserListResponse,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, session: Session = Depends(get_db_session)):
    """Register a new user.
    
    Args:
        data: Registration data (username, password).
        session: Database session.
        
    Returns:
        Created user info.
        
    Raises:
        ApiError: If username is taken or is reserved.
    """
    # Check if username is reserved (admin username)
    if data.username.lower() == settings.admin_username.lower():
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.USERNAME_RESERVED, "该用户名为系统保留，无法注册")
    
    # Check if username already exists
    existing_user = session.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.USERNAME_EXISTS, "用户名已存在")
    
    # Create new user
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        is_admin=False,
        must_change_password=False,
    )
    session.add(user)
    session.flush()
    
    # Create default settings for the user
    user_settings = UserSettings(
        user_id=user.id,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        request_delay=settings.request_delay,
    )
    session.add(user_settings)
    
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, session: Session = Depends(get_db_session)):
    """Login and get JWT tokens.
    
    Args:
        data: Login credentials (username, password).
        session: Database session.
        
    Returns:
        Access and refresh tokens.
        
    Raises:
        ApiError: If credentials are invalid.
    """
    # Find user
    user = session.query(User).filter(User.username == data.username).first()
    if not user or not user.password_hash:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.INVALID_CREDENTIALS, "用户名或密码错误")
    
    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise_api_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.INVALID_CREDENTIALS, "用户名或密码错误")
    
    # Upgrade hashes written before the bcrypt migration
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(data.password)
    
    # Create tokens
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        must_change_password=user.must_change_password,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: TokenRefresh, session: Session = Depends(get_db_session)):
    """Refresh access token using refresh token.
    
    Args:
        data: Refresh token.
        session: Database session.
        
    Returns:
        New access and refresh tokens.
        
    Raises:
        ApiError: If refresh token is invalid.
    """
    payload = verify_refresh_token(data.refresh_token)
    if not payload:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.REFRESH_TOKEN_INVALID, "Refresh Token 无效或已过期")
    
    user_id = payload.get("sub")
    user = session.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise_api_error(status.HTTP_401_UNAUTHORIZED, ErrorCode.USER_NOT_FOUND, "用户不存在")
    
    # Create new tokens
    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        must_change_password=user.must_change_password,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info.
    
    Args:
        current_user: Authenticated user.
        
    Returns:
        User info.
    """
    return current_user


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Change current user's password.
    
    Args:
        data: Current and new password.
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        Success message.
        
    Raises:
        ApiError: If current password is wrong.
    """
    # Verify current password
    if not current_user.password_hash or not verify_password(data.current_password, current_user.password_hash):
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.CURRENT_PASSWORD_WRONG, "当前密码错误")
    
    # Update password
    user = session.query(User).filter(User.id == current_user.id).first()
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    
    return MessageResponse(message="密码修改成功")


# ============= Admin Routes =============

admin_router = APIRouter(prefix="/admin", tags=["管理员"])


@admin_router.get("/users", response_model=list[UserListResponse])
def list_users(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_db_session),
):
    """List all users (admin only).
    
    Args:
        admin_user: Admin user.
        session: Database session.
        
    Returns:
        List of all users.
    """
    users = session.query(User).order_by(User.created_at.desc()).all()
    return users


@admin_router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
def reset_user_password(
    user_id: int,
    data: PasswordReset,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_db_session),
):
    """Reset a user's password (admin only).
    
    Args:
        user_id: Target user ID.
        data: New password.
        admin_user: Admin user.
        session: Database session.
        
    Returns:
        Success message.
        
    Raises:
        ApiError: If user not found.
    """
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.USER_NOT_FOUND, "用户不存在")
    
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    
    return MessageResponse(message=f"用户 {user.username} 的密码已重置")
