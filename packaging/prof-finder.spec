# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path


repo_root = Path(SPECPATH).parent
one_dir = os.getenv("PROF_FINDER_PYINSTALLER_MODE") == "onedir" or sys.platform.startswith("linux")

datas = [
    (str(repo_root / "frontend" / "dist"), "frontend_dist"),
    (str(repo_root / "backend" / "prof_finder" / "prompts"), "prof_finder/prompts"),
]

hiddenimports = [
    "sentence_transformers",
    "sklearn",
]

a = Analysis(
    [str(repo_root / "backend" / "prof_finder" / "launcher.py")],
    pathex=[str(repo_root / "backend")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

if one_dir:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="Prof-Finder",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="Prof-Finder",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="Prof-Finder",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
