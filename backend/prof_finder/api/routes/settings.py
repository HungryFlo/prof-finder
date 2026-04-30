"""User settings API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.schema import User, UserSettings
from ...config import settings as app_settings
from ..deps import get_db_session, get_current_user
from ..schemas import (
    UserSettingsUpdate,
    UserSettingsResponse,
    MessageResponse,
)

router = APIRouter(prefix="/settings", tags=["设置"])


def mask_api_key(key: str | None) -> str | None:
    """Mask an API key for display (show first 4 and last 4 chars).
    
    Args:
        key: API key to mask.
        
    Returns:
        Masked key string or None.
    """
    if not key:
        return None
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


@router.get("", response_model=UserSettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get current user's settings.
    
    Args:
        current_user: Authenticated user.
        session: Database session.
        
    Returns:
        User settings with masked API key.
    """
    user_settings = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )
    
    if not user_settings:
        # Create default settings if not exists
        user_settings = UserSettings(
            user_id=current_user.id,
            deepseek_base_url=app_settings.deepseek_base_url,
            request_delay=app_settings.request_delay,
        )
        session.add(user_settings)
        session.flush()
        session.refresh(user_settings)
    
    return UserSettingsResponse(
        deepseek_api_key_masked=mask_api_key(user_settings.deepseek_api_key),
        deepseek_base_url=user_settings.deepseek_base_url or app_settings.deepseek_base_url,
        request_delay=user_settings.request_delay or app_settings.request_delay,
    )


@router.put("", response_model=UserSettingsResponse)
def update_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update current user's settings.

    Args:
        data: Settings to update.
        current_user: Authenticated user.
        session: Database session.

    Returns:
        Updated settings with masked API key.
    """
    user_settings = (
        session.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )

    if not user_settings:
        # Create settings if not exists
        user_settings = UserSettings(
            user_id=current_user.id,
            deepseek_base_url=app_settings.deepseek_base_url,
            request_delay=app_settings.request_delay,
        )
        session.add(user_settings)
        session.flush()

    # Update fields
    if data.deepseek_api_key is not None:
        user_settings.deepseek_api_key = data.deepseek_api_key
    if data.deepseek_base_url is not None:
        user_settings.deepseek_base_url = data.deepseek_base_url
    if data.request_delay is not None:
        user_settings.request_delay = data.request_delay

    session.flush()
    session.refresh(user_settings)

    return UserSettingsResponse(
        deepseek_api_key_masked=mask_api_key(user_settings.deepseek_api_key),
        deepseek_base_url=user_settings.deepseek_base_url or app_settings.deepseek_base_url,
        request_delay=user_settings.request_delay or app_settings.request_delay,
    )
