"""Tests for portable install configuration and uninstall script generation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from prof_finder.packaging.paths import PathValidationError, validate_data_dir
from prof_finder.packaging.uninstall import write_uninstall_scripts
from prof_finder.runtime import (
    INSTALL_CONFIG_NAME,
    apply_install_config,
    install_config_path,
    is_configured,
    load_install_config,
    model_dir_for_data_root,
    save_install_config,
)


@pytest.fixture
def portable_env(monkeypatch, tmp_path):
    install = tmp_path / "app"
    install.mkdir()
    fake_exe = install / "Prof-Finder.exe"
    fake_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    monkeypatch.setenv("PROF_FINDER_PACKAGED", "1")
    monkeypatch.delenv("PROF_FINDER_DATA_DIR", raising=False)
    monkeypatch.delenv("PROF_FINDER_MODEL_DIR", raising=False)
    return install


def test_save_and_load_install_config(portable_env):
    data_dir = portable_env.parent / "data-root"
    model_dir = model_dir_for_data_root(data_dir)
    save_install_config(data_dir, model_dir)

    config_path = portable_env / INSTALL_CONFIG_NAME
    assert config_path.is_file()
    loaded = load_install_config()
    assert loaded is not None
    assert loaded["data_dir"] == str(data_dir.resolve())
    assert loaded["model_dir"] == str(model_dir.resolve())


def test_apply_install_config_sets_environment(portable_env, monkeypatch):
    data_dir = portable_env.parent / "pf-data"
    model_dir = model_dir_for_data_root(data_dir)
    save_install_config(data_dir, model_dir)

    apply_install_config()
    assert os.environ["PROF_FINDER_DATA_DIR"] == str(data_dir.resolve())
    assert os.environ["PROF_FINDER_MODEL_DIR"] == str(model_dir.resolve())


def test_is_configured_follows_install_json(portable_env):
    assert not is_configured()
    save_install_config(portable_env.parent / "data", model_dir_for_data_root(portable_env.parent / "data"))
    assert is_configured()


def test_validate_data_dir_rejects_install_subfolder(portable_env):
    nested = portable_env / "nested-data"
    with pytest.raises(PathValidationError, match="程序安装目录"):
        validate_data_dir(nested, portable_env)


def test_validate_data_dir_rejects_home(portable_env, monkeypatch):
    monkeypatch.setattr(
        "prof_finder.packaging.paths.Path.home",
        lambda: portable_env,
    )
    with pytest.raises(PathValidationError, match="主目录"):
        validate_data_dir(portable_env, portable_env)


def test_write_uninstall_scripts_embed_paths(portable_env):
    data_dir = portable_env.parent / "user-data"
    model_dir = model_dir_for_data_root(data_dir)
    write_uninstall_scripts(portable_env, data_dir, model_dir)

    if sys.platform == "win32":
        script = portable_env / "uninstall-prof-finder.bat"
        content = script.read_text(encoding="utf-8")
    else:
        script = portable_env / "uninstall-prof-finder.sh"
        content = script.read_text(encoding="utf-8")

    assert str(data_dir.resolve()) in content
    assert str(model_dir.resolve()) in content
    assert "MODEL_DIR" in content
