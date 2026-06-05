"""Configuration management for Prof-Finder."""

import os
import secrets
from dataclasses import dataclass

from .runtime import is_configured, is_packaged, load_runtime_environment, runtime_file

if not is_packaged() or is_configured():
    load_runtime_environment()


def _env(name: str, legacy: str | None = None, default: str = "") -> str:
    value = os.getenv(name)
    if value is not None and str(value).strip():
        return str(value).strip()
    if legacy:
        legacy_value = os.getenv(legacy)
        if legacy_value is not None and str(legacy_value).strip():
            return str(legacy_value).strip()
    return default


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # LLM API (OpenAI-compatible or Anthropic)
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str

    # Database
    database_path: str

    # Crawler
    request_delay: int
    scholarly_proxy: str | None

    # Professor auto-enrichment (Scholar publications → summaries + profile)
    professor_enrichment_max_publications: int

    # Default user (for CLI)
    default_user: str

    # Admin account
    admin_username: str
    admin_password: str

    # Huey task queue
    huey_db_path: str
    huey_consumer_workers: int

    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables."""
        use_packaged_paths = is_packaged() and is_configured()
        default_database_path = (
            str(runtime_file("prof_finder.db")) if use_packaged_paths else "./data/prof_finder.db"
        )
        default_huey_db_path = (
            str(runtime_file("huey_tasks.db")) if use_packaged_paths else "./data/huey_tasks.db"
        )

        provider = _env("LLM_PROVIDER", default="openai").lower()
        if provider not in {"openai", "anthropic"}:
            provider = "openai"

        default_base_url = (
            "https://api.anthropic.com"
            if provider == "anthropic"
            else _env("LLM_BASE_URL", "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        )

        return cls(
            llm_provider=provider,
            llm_api_key=_env("LLM_API_KEY", "DEEPSEEK_API_KEY"),
            llm_base_url=_env("LLM_BASE_URL", "DEEPSEEK_BASE_URL", default_base_url),
            llm_model=_env("LLM_MODEL", "DEEPSEEK_MODEL", "deepseek-chat"),
            database_path=os.getenv("DATABASE_PATH", default_database_path),
            request_delay=int(os.getenv("REQUEST_DELAY", "3")),
            scholarly_proxy=os.getenv("SCHOLARLY_PROXY") or None,
            professor_enrichment_max_publications=int(
                os.getenv("PROFESSOR_ENRICHMENT_MAX_PUBLICATIONS", "15")
            ),
            huey_db_path=os.getenv("HUEY_DB_PATH", default_huey_db_path),
            huey_consumer_workers=int(os.getenv("HUEY_CONSUMER_WORKERS", "2")),
            default_user=os.getenv("DEFAULT_USER", "default"),
            admin_username=os.getenv("ADMIN_USERNAME", "root"),
            admin_password=os.getenv("ADMIN_PASSWORD", "root123"),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        )

    # Backward-compatible aliases for legacy code paths
    @property
    def deepseek_api_key(self) -> str:
        return self.llm_api_key

    @property
    def deepseek_base_url(self) -> str:
        return self.llm_base_url

    @property
    def deepseek_model(self) -> str:
        return self.llm_model

    def validate(self) -> list[str]:
        """Validate settings and return list of errors."""
        errors = []
        if not self.llm_api_key:
            errors.append("LLM_API_KEY (or legacy DEEPSEEK_API_KEY) is not configured")
        if not self.llm_model:
            errors.append("LLM_MODEL (or legacy DEEPSEEK_MODEL) is not configured")
        return errors

    @property
    def is_default_admin_password(self) -> bool:
        """Check if using the default admin password."""
        return self.admin_password == "root123"


# Global settings instance
settings = Settings.load()
