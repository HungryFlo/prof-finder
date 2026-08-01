"""Authentication utilities: password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import hashlib
import secrets

import bcrypt
from jose import JWTError, jwt

from ..config import settings

_BCRYPT_ROUNDS = 12
_BCRYPT_PREFIX = "$2"


def _prepare_secret(password: str) -> bytes:
    """Reduce a password to a fixed-size token accepted by bcrypt.

    bcrypt silently truncates input beyond 72 bytes, which a 100-character
    password can exceed once encoded as UTF-8. Digesting first preserves the
    full password's entropy.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def _hash_with_salt(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256 (legacy scheme)."""
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _verify_legacy(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against the pre-bcrypt 'salt$sha256' format."""
    try:
        salt, stored_hash = hashed_password.split("$", 1)
    except ValueError:
        return False
    return secrets.compare_digest(_hash_with_salt(plain_password, salt), stored_hash)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        Bcrypt hash string (``$2b$...``).
    """
    return bcrypt.hashpw(_prepare_secret(password), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its stored hash.

    Accepts both bcrypt hashes and the legacy 'salt$sha256' format so that
    databases created before the bcrypt migration keep working.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.

    Returns:
        True if password matches, False otherwise.
    """
    if not hashed_password:
        return False
    if not hashed_password.startswith(_BCRYPT_PREFIX):
        return _verify_legacy(plain_password, hashed_password)
    try:
        return bcrypt.checkpw(_prepare_secret(plain_password), hashed_password.encode())
    except ValueError:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Report whether a stored hash uses the legacy scheme and should be upgraded."""
    return bool(hashed_password) and not hashed_password.startswith(_BCRYPT_PREFIX)


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
