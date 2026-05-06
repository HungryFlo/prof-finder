"""Runtime path helpers for development and packaged local-app modes."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv

APP_NAME = "Prof-Finder"
PACKAGE_ENV = "PROF_FINDER_PACKAGED"
DATA_DIR_ENV = "PROF_FINDER_DATA_DIR"
FRONTEND_DIST_ENV = "PROF_FINDER_FRONTEND_DIST"


def is_packaged() -> bool:
    """Return whether the app is running from the portable launcher/package."""
    return os.getenv(PACKAGE_ENV) == "1" or bool(getattr(sys, "frozen", False))


def package_root() -> Path:
    """Return the PyInstaller extraction root or repository root."""
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def user_data_dir() -> Path:
    """Return the per-user data directory used by packaged mode."""
    override = os.getenv(DATA_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    base = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "prof-finder"


def runtime_file(name: str) -> Path:
    """Return a file path inside the packaged runtime data directory."""
    data_dir = user_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / name


def logs_dir() -> Path:
    """Return the packaged runtime log directory."""
    path = user_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def frontend_dist_dir() -> Path | None:
    """Return the built frontend directory if it is available."""
    candidates: list[Path] = []
    if os.getenv(FRONTEND_DIST_ENV):
        candidates.append(Path(os.environ[FRONTEND_DIST_ENV]).expanduser())

    root = package_root()
    candidates.extend(
        [
            root / "frontend_dist",
            root / "frontend" / "dist",
            Path(__file__).resolve().parents[2] / "frontend" / "dist",
        ]
    )

    for candidate in candidates:
        if (candidate / "index.html").is_file():
            return candidate.resolve()
    return None


def load_runtime_environment() -> None:
    """Load development and packaged runtime environment files."""
    if not is_packaged():
        load_dotenv()
        return

    env_path = runtime_file("runtime.env")
    if not env_path.exists():
        env_path.write_text(
            f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}\n",
            encoding="utf-8",
        )
    load_dotenv(env_path, override=False)
