"""Validation helpers for portable install storage paths."""

from __future__ import annotations

from pathlib import Path


class PathValidationError(ValueError):
    """Raised when a user-selected storage path is unsafe or unusable."""


def validate_data_dir(data_dir: Path, install_dir: Path) -> Path:
    """Validate and resolve a user-selected data root directory."""
    resolved = data_dir.expanduser().resolve()
    home = Path.home().resolve()

    if not resolved.name:
        raise PathValidationError("数据目录路径无效")
    if resolved == Path("/").resolve():
        raise PathValidationError("不能选择根目录")
    if resolved == home:
        raise PathValidationError("不能选择用户主目录")
    if resolved.parent == resolved:
        raise PathValidationError("不能选择根目录")

    install_resolved = install_dir.resolve()
    if resolved == install_resolved or resolved.is_relative_to(install_resolved):
        raise PathValidationError("数据目录不能位于程序安装目录内")

    resolved.mkdir(parents=True, exist_ok=True)
    probe = resolved / ".write-test"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise PathValidationError(f"目录不可写: {exc}") from exc

    return resolved
