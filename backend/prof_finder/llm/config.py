"""Resolve LLM API configuration from user settings and environment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Optional

if TYPE_CHECKING:
    from ..config import Settings
    from ..models.schema import UserSettings

LLMProviderType = Literal["openai", "anthropic"]

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"


@dataclass(frozen=True)
class LLMConfig:
    """User- or deployment-level LLM endpoint configuration."""

    provider: LLMProviderType
    api_key: str
    base_url: str
    model: str

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in {"test_key", "your_api_key_here"})


def _first_non_empty(*values: Optional[str]) -> Optional[str]:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _normalize_provider(value: Optional[str]) -> LLMProviderType:
    if value and value.strip().lower() == "anthropic":
        return "anthropic"
    return "openai"


def _field(row: Any, *names: str) -> Optional[str]:
    for name in names:
        if row is None:
            return None
        value = getattr(row, name, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def resolve_llm_config(
    user_settings: Optional["UserSettings"] = None,
    app_settings: Optional["Settings"] = None,
) -> LLMConfig:
    """Merge per-user settings with deployment defaults (user wins)."""
    from ..config import settings as default_app_settings

    app = app_settings or default_app_settings

    provider = _normalize_provider(
        _first_non_empty(
            _field(user_settings, "llm_provider"),
            getattr(app, "llm_provider", None),
        )
    )

    api_key = _first_non_empty(
        _field(user_settings, "llm_api_key", "deepseek_api_key"),
        getattr(app, "llm_api_key", None),
        getattr(app, "deepseek_api_key", None),
    ) or ""

    model = _first_non_empty(
        _field(user_settings, "llm_model", "deepseek_model"),
        getattr(app, "llm_model", None),
        getattr(app, "deepseek_model", None),
    ) or ""

    base_url = _first_non_empty(
        _field(user_settings, "llm_base_url", "deepseek_base_url"),
        getattr(app, "llm_base_url", None),
        getattr(app, "deepseek_base_url", None),
    )

    if not base_url:
        base_url = (
            DEFAULT_ANTHROPIC_BASE_URL
            if provider == "anthropic"
            else DEFAULT_OPENAI_BASE_URL
        )

    return LLMConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def llm_not_configured_message() -> str:
    return "请先在设置中配置 LLM API Key"


def llm_provider_for_user_settings(
    user_settings: Optional["UserSettings"] = None,
    app_settings: Optional["Settings"] = None,
):
    """Build an :class:`LLMProvider` from resolved configuration."""
    from ..ai_workflows.provider import LLMProvider

    return LLMProvider(config=resolve_llm_config(user_settings, app_settings))
