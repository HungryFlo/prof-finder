"""Authentication utilities: password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets

from jose import JWTError, jwt

from ..config import settings


def _hash_with_salt(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256."""
    return hashlib.sha256((salt + password).encode()).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with random salt.
    
    Args:
        password: Plain text password.
        
    Returns:
        Hashed password string in format 'salt$hash'.
    """
    salt = secrets.token_hex(16)
    hash_value = _hash_with_salt(password, salt)
    return f"{salt}${hash_value}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.
        
    Returns:
        True if password matches, False otherwise.
    """
    try:
        salt, stored_hash = hashed_password.split("$", 1)
        return secrets.compare_digest(_hash_with_salt(plain_password, salt), stored_hash)
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.
    
    Args:
        data: Data to encode in the token.
        expires_delta: Optional custom expiration time.
        
    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token.
        expires_delta: Optional custom expiration time.
        
    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode.
        
    Returns:
        Decoded token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[dict]:
    """Verify an access token and return its payload.
    
    Args:
        token: JWT access token to verify.
        
    Returns:
        Token payload if valid access token, None otherwise.
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify a refresh token and return its payload.
    
    Args:
        token: JWT refresh token to verify.
        
    Returns:
        Token payload if valid refresh token, None otherwise.
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None
