"""User settings API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...config import settings as app_settings
from ...llm.config import resolve_llm_config
from ...models.schema import User, UserSettings
from ..deps import get_current_user, get_db_session
from ..schemas import UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/settings", tags=["设置"])


def mask_api_key(key: str | None) -> str | None:
    """Mask an API key for display (show first 4 and last 4 chars)."""
    if not key:
        return None
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


def _stored_api_key(user_settings: UserSettings | None) -> str | None:
    if not user_settings:
        return None
    return user_settings.llm_api_key or user_settings.deepseek_api_key


def _settings_response(user_settings: UserSettings) -> UserSettingsResponse:
    config = resolve_llm_config(user_settings, app_settings)
    return UserSettingsResponse(
        llm_provider=config.provider,
        llm_api_key_masked=mask_api_key(_stored_api_key(user_settings)),
        llm_base_url=config.base_url,
        llm_model=config.model,
        request_delay=user_settings.request_delay or app_settings.request_delay,
        auto_enrich_on_save_fetch_publication_details=bool(
            user_settings.auto_enrich_on_save_fetch_publication_details
        ),
        auto_enrich_on_save_paper_summaries=bool(
            user_settings.auto_enrich_on_save_paper_summaries
        ),
        auto_enrich_on_save_research_profile=bool(
            user_settings.auto_enrich_on_save_research_profile
        ),
    )


def _default_user_settings(user_id: int) -> UserSettings:
    return UserSettings(
        user_id=user_id,
        llm_provider=app_settings.llm_provider,
        llm_base_url=app_settings.llm_base_url,
        llm_model=app_settings.llm_model,
        request_delay=app_settings.request_delay,
    )


@router.get("", response_model=UserSettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Get current user's settings."""
    user_settings = (
        session.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    )

    if not user_settings:
        user_settings = _default_user_settings(current_user.id)
        session.add(user_settings)
        session.flush()
        session.refresh(user_settings)

    return _settings_response(user_settings)


@router.put("", response_model=UserSettingsResponse)
def update_settings(
    data: UserSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
):
    """Update current user's settings."""
    user_settings = (
        session.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    )

    if not user_settings:
        user_settings = _default_user_settings(current_user.id)
        session.add(user_settings)
        session.flush()

    if data.llm_provider is not None:
        user_settings.llm_provider = data.llm_provider
    if data.llm_api_key is not None:
        user_settings.llm_api_key = data.llm_api_key
        user_settings.deepseek_api_key = data.llm_api_key
    if data.llm_base_url is not None:
        user_settings.llm_base_url = data.llm_base_url
        user_settings.deepseek_base_url = data.llm_base_url
    if data.llm_model is not None:
        user_settings.llm_model = data.llm_model
        user_settings.deepseek_model = data.llm_model
    if data.request_delay is not None:
        user_settings.request_delay = data.request_delay
    if data.auto_enrich_on_save_fetch_publication_details is not None:
        user_settings.auto_enrich_on_save_fetch_publication_details = (
            data.auto_enrich_on_save_fetch_publication_details
        )
    if data.auto_enrich_on_save_paper_summaries is not None:
        user_settings.auto_enrich_on_save_paper_summaries = data.auto_enrich_on_save_paper_summaries
    if data.auto_enrich_on_save_research_profile is not None:
        user_settings.auto_enrich_on_save_research_profile = (
            data.auto_enrich_on_save_research_profile
        )

    session.flush()
    session.refresh(user_settings)
    return _settings_response(user_settings)
