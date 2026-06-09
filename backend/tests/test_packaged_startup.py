"""Tests for packaged-mode startup before first-run setup completes."""

from __future__ import annotations

import sys

import pytest

from prof_finder.runtime import save_install_config, model_dir_for_data_root


@pytest.fixture
def portable_env(monkeypatch, tmp_path):
    install = tmp_path / "app"
    install.mkdir()
    fake_exe = install / "Prof-Finder"
    fake_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    monkeypatch.setenv("PROF_FINDER_PACKAGED", "1")
    monkeypatch.delenv("PROF_FINDER_DATA_DIR", raising=False)
    monkeypatch.delenv("PROF_FINDER_MODEL_DIR", raising=False)
    return install


def test_unconfigured_packaged_import_does_not_open_database(portable_env, monkeypatch):
    """Importing the API app must not touch SQLite before install.json exists."""
    monkeypatch.chdir("/")

    from prof_finder.api.main import app

    paths = {route.path for route in app.routes}
    assert "/api/health" in paths
    assert "/api/setup/status" in paths


def test_huey_not_initialized_before_setup(portable_env, monkeypatch):
    """Huey must stay uninitialized until setup completes."""
    monkeypatch.chdir("/")

    import prof_finder.api.task_queue as tq

    tq._huey = None
    tq._huey_run_task_fn = None

    with pytest.raises(RuntimeError, match="setup"):
        tq._ensure_huey()


def test_huey_initializes_after_setup(portable_env, monkeypatch, tmp_path):
    data_dir = tmp_path / "user-data"
    save_install_config(data_dir, model_dir_for_data_root(data_dir))

    import prof_finder.api.task_queue as tq
    from prof_finder.runtime import apply_install_config

    apply_install_config()
    tq._huey = None
    tq._huey_run_task_fn = None

    huey = tq._ensure_huey()
    assert huey is not None
