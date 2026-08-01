"""FastAPI dependencies for authentication and database access."""

from typing import Generator, Optional

from fastapi import Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.database import get_db, Database
from ..models.schema import User
from .auth import verify_access_token, verify_stream_token
from .errors import ErrorCode, raise_api_error

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def get_db_session() -> Generator[Session, None, None]:
    """Get a database session for FastAPI dependency injection.
    
    Yields:
        SQLAlchemy session that auto-commits on success, rollbacks on error.
    """
    db = get_db()
    session = db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_db_session),
) -> User:
    """Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request header.
        session: Database session.
        
    Returns:
        Authenticated User instance.
        
    Raises:
        ApiError: If token is missing, invalid, or user not found.
    """
    auth_headers = {"WWW-Authenticate": "Bearer"}
    if not credentials:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTH_REQUIRED,
            "未提供认证信息",
            headers=auth_headers,
        )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if not payload:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.TOKEN_INVALID,
            "Token 无效或已过期",
            headers=auth_headers,
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.TOKEN_MALFORMED,
            "Token 格式无效",
            headers=auth_headers,
        )
    
    user = session.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.USER_NOT_FOUND,
            "用户不存在",
            headers=auth_headers,
        )
    
    return user


def get_current_user_sse(
    token: Optional[str] = Query(None, description="JWT token (for EventSource clients)"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_db_session),
) -> User:
    """Get the current user from a JWT token supplied either as a query parameter
    or as an HTTP Bearer Authorization header.

    The query-parameter form exists because the browser's native EventSource API
    does not support custom request headers.

    Args:
        token: JWT token passed as ``?token=<value>``.
        credentials: HTTP Bearer credentials from the Authorization header.
        session: Database session.

    Returns:
        Authenticated User instance.

    Raises:
        ApiError: If no valid token is provided.
    """
    auth_headers = {"WWW-Authenticate": "Bearer"}
    raw_token: Optional[str] = None
    if token:
        raw_token = token
    elif credentials:
        raw_token = credentials.credentials

    if not raw_token:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTH_REQUIRED,
            "未提供认证信息",
            headers=auth_headers,
        )

    # Prefer short-lived stream tickets in the query string; still accept access JWTs.
    payload = verify_stream_token(raw_token) or verify_access_token(raw_token)
    if not payload:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.TOKEN_INVALID,
            "Token 无效或已过期",
            headers=auth_headers,
        )

    user_id = payload.get("sub")
    if not user_id:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.TOKEN_MALFORMED,
            "Token 格式无效",
            headers=auth_headers,
        )

    user = session.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise_api_error(
            status.HTTP_401_UNAUTHORIZED,
            ErrorCode.USER_NOT_FOUND,
            "用户不存在",
            headers=auth_headers,
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and verify they don't need to change password.
    
    For most endpoints, we allow access even if must_change_password is True,
    but some sensitive operations might want to check this.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        User instance.
    """
    return current_user


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current user and verify they are an admin.
    
    Args:
        current_user: Current authenticated user.
        
    Returns:
        Admin User instance.
        
    Raises:
        ApiError: If user is not an admin.
    """
    if not current_user.is_admin:
        raise_api_error(
            status.HTTP_403_FORBIDDEN,
            ErrorCode.ADMIN_REQUIRED,
            "权限不足，需要管理员权限",
        )
    return current_user
