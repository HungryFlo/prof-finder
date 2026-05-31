"""Runtime path helpers for development and packaged local-app modes."""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

APP_NAME = "Prof-Finder"
PACKAGE_ENV = "PROF_FINDER_PACKAGED"
DATA_DIR_ENV = "PROF_FINDER_DATA_DIR"
MODEL_DIR_ENV = "PROF_FINDER_MODEL_DIR"
FRONTEND_DIST_ENV = "PROF_FINDER_FRONTEND_DIST"
INSTALL_CONFIG_NAME = "install.json"
MODEL_SUBDIR = Path("models") / "qwen3-embedding-0.6b"


def is_packaged() -> bool:
    """Return whether the app is running from the portable launcher/package."""
    return os.getenv(PACKAGE_ENV) == "1" or bool(getattr(sys, "frozen", False))


def install_dir() -> Path:
    """Return the directory containing the Prof-Finder executable."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def install_config_path() -> Path:
    """Return the path to install.json beside the packaged executable."""
    return install_dir() / INSTALL_CONFIG_NAME


def is_configured() -> bool:
    """Return whether packaged storage paths have been set up."""
    if not is_packaged():
        return True
    return install_config_path().is_file()


def default_suggested_data_dir() -> Path:
    """Return the platform default data directory shown in first-run setup."""
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "prof-finder"


def model_dir_for_data_root(data_dir: Path) -> Path:
    """Return the embedding model directory under a data root."""
    return data_dir.resolve() / MODEL_SUBDIR


def load_install_config() -> dict[str, Any] | None:
    """Load install.json if present."""
    path = install_config_path()
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_install_config(data_dir: Path, model_dir: Path) -> None:
    """Persist install.json beside the executable."""
    payload = {
        "data_dir": str(data_dir.resolve()),
        "model_dir": str(model_dir.resolve()),
    }
    install_config_path().write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def apply_install_config() -> None:
    """Apply install.json paths to environment variables before settings load."""
    if os.getenv(DATA_DIR_ENV) or os.getenv(MODEL_DIR_ENV):
        return
    config = load_install_config()
    if not config:
        return
    data_dir = config.get("data_dir")
    model_dir = config.get("model_dir")
    if data_dir:
        os.environ[DATA_DIR_ENV] = str(Path(data_dir).expanduser().resolve())
    if model_dir:
        os.environ[MODEL_DIR_ENV] = str(Path(model_dir).expanduser().resolve())


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

    if is_packaged():
        return default_suggested_data_dir()

    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    base = Path(os.getenv("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "prof-finder"


def model_dir() -> Path:
    """Return the local embedding model directory."""
    override = os.getenv(MODEL_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if is_packaged() and is_configured():
        return model_dir_for_data_root(user_data_dir())
    return Path(__file__).resolve().parents[2] / MODEL_SUBDIR


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

    if not is_configured():
        return

    env_path = runtime_file("runtime.env")
    if not env_path.exists():
        env_path.write_text(
            f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}\n",
            encoding="utf-8",
        )
    load_dotenv(env_path, override=False)
