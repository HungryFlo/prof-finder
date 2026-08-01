"""First-run data directory validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from prof_finder.packaging.paths import PathValidationError, validate_data_dir


def test_creates_and_resolves_the_directory(tmp_path):
    target = tmp_path / "data" / "prof-finder"
    resolved = validate_data_dir(target, tmp_path / "app")
    assert resolved == target.resolve()
    assert resolved.is_dir()


def test_accepts_an_existing_directory(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    assert validate_data_dir(target, tmp_path / "app") == target.resolve()


def test_leaves_no_probe_file_behind(tmp_path):
    resolved = validate_data_dir(tmp_path / "data", tmp_path / "app")
    assert list(resolved.iterdir()) == []


def test_expands_a_user_relative_path(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    resolved = validate_data_dir(Path("~/pf-data"), tmp_path / "app")
    assert resolved == (home / "pf-data").resolve()


def test_rejects_the_filesystem_root():
    with pytest.raises(PathValidationError):
        validate_data_dir(Path("/"), Path("/opt/app"))


def test_rejects_the_home_directory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    with pytest.raises(PathValidationError, match="主目录"):
        validate_data_dir(home, tmp_path / "app")


def test_rejects_the_install_directory(tmp_path):
    install = tmp_path / "app"
    install.mkdir()
    with pytest.raises(PathValidationError, match="安装目录"):
        validate_data_dir(install, install)


def test_rejects_a_path_inside_the_install_directory(tmp_path):
    install = tmp_path / "app"
    install.mkdir()
    with pytest.raises(PathValidationError, match="安装目录"):
        validate_data_dir(install / "data", install)


def test_rejects_an_unwritable_directory(tmp_path):
    target = tmp_path / "readonly"
    target.mkdir()
    target.chmod(0o500)
    try:
        with pytest.raises(PathValidationError, match="不可写"):
            validate_data_dir(target, tmp_path / "app")
    finally:
        target.chmod(0o700)
