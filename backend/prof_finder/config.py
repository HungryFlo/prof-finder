"""Configuration management for Prof-Finder."""

import os
import secrets
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # DeepSeek API
    deepseek_api_key: str
    deepseek_base_url: str

    # Database
    database_path: str

    # Crawler
    request_delay: int
    scholarly_proxy: str | None

    # Default user (for CLI)
    default_user: str

    # Admin account
    admin_username: str
    admin_password: str

    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    @classmethod
    def load(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            database_path=os.getenv("DATABASE_PATH", "./data/prof_finder.db"),
            request_delay=int(os.getenv("REQUEST_DELAY", "3")),
            scholarly_proxy=os.getenv("SCHOLARLY_PROXY") or None,
            default_user=os.getenv("DEFAULT_USER", "default"),
            # Admin account
            admin_username=os.getenv("ADMIN_USERNAME", "root"),
            admin_password=os.getenv("ADMIN_PASSWORD", "root123"),
            # JWT settings
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        )

    def validate(self) -> list[str]:
        """Validate settings and return list of errors."""
        errors = []
        if not self.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is not configured")
        return errors

    @property
    def is_default_admin_password(self) -> bool:
        """Check if using the default admin password."""
        return self.admin_password == "root123"


# Global settings instance
settings = Settings.load()
