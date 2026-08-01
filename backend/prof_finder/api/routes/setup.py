"""First-run storage setup API for packaged mode."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from ...packaging.paths import PathValidationError, validate_data_dir
from ...packaging.uninstall import write_uninstall_scripts
from ...runtime import (
    default_suggested_data_dir,
    install_dir,
    is_configured,
    is_packaged,
    model_dir_for_data_root,
    save_install_config,
)
from ..errors import ErrorCode, raise_api_error

router = APIRouter(prefix="/setup", tags=["首次配置"])


class SetupStatusResponse(BaseModel):
    packaged: bool
    configured: bool
    suggested_data_dir: str | None = None


class PickDirectoryResponse(BaseModel):
    path: str


class SetupCompleteRequest(BaseModel):
    data_dir: str = Field(..., min_length=1)


class SetupCompleteResponse(BaseModel):
    restart_required: bool = True
    data_dir: str
    model_dir: str


def _require_setup_allowed() -> None:
    if not is_packaged():
        raise_api_error(status.HTTP_404_NOT_FOUND, ErrorCode.SETUP_PACKAGED_ONLY, "Setup is only available in packaged mode")
    if is_configured():
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.SETUP_ALREADY_COMPLETED, "Setup has already been completed")


@router.get("/status", response_model=SetupStatusResponse)
def get_setup_status() -> SetupStatusResponse:
    packaged = is_packaged()
    configured = is_configured()
    suggested = None
    if packaged and not configured:
        suggested = str(default_suggested_data_dir())
    return SetupStatusResponse(
        packaged=packaged,
        configured=configured,
        suggested_data_dir=suggested,
    )


@router.post("/pick-directory", response_model=PickDirectoryResponse)
def pick_directory() -> PickDirectoryResponse:
    _require_setup_allowed()
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        raise_api_error(status.HTTP_503_SERVICE_UNAVAILABLE, ErrorCode.FOLDER_PICKER_UNAVAILABLE, "无法打开文件夹选择对话框，请手动输入路径")

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(
            title="选择 Prof-Finder 数据存储目录",
            initialdir=str(default_suggested_data_dir().parent),
        )
    finally:
        root.destroy()

    if not selected:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.NO_DIRECTORY_SELECTED, "未选择目录")
    return PickDirectoryResponse(path=str(Path(selected).resolve()))


@router.post("/complete", response_model=SetupCompleteResponse)
def complete_setup(body: SetupCompleteRequest) -> SetupCompleteResponse:
    _require_setup_allowed()

    try:
        data_path = validate_data_dir(Path(body.data_dir), install_dir())
    except PathValidationError as exc:
        raise_api_error(status.HTTP_400_BAD_REQUEST, ErrorCode.SETUP_FAILED, str(exc))

    model_path = model_dir_for_data_root(data_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    save_install_config(data_path, model_path)
    write_uninstall_scripts(install_dir(), data_path, model_path)

    subprocess.Popen(
        [sys.executable],
        cwd=str(install_dir()),
        close_fds=True,
    )
    os._exit(0)
