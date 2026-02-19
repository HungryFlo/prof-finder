"""FastAPI dependencies for authentication and database access."""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.database import get_db, Database
from ..models.schema import User
from .auth import verify_access_token

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
        HTTPException: If token is missing, invalid, or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = session.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
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
        HTTPException: If no valid token is provided.
    """
    raw_token: Optional[str] = None
    if token:
        raw_token = token
    elif credentials:
        raw_token = credentials.credentials

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 格式无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
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
        HTTPException: If user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限",
        )
    return current_user
