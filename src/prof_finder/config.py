"""Configuration management for Prof-Finder."""

import os
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

    # Default user
    default_user: str

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
        )

    def validate(self) -> list[str]:
        """Validate settings and return list of errors."""
        errors = []
        if not self.deepseek_api_key:
            errors.append("DEEPSEEK_API_KEY is not configured")
        return errors


# Global settings instance
settings = Settings.load()
