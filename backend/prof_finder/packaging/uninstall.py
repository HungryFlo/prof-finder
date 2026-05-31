"""Generate platform-specific portable uninstall scripts."""

from __future__ import annotations

import sys
from pathlib import Path


def _escape_windows_path(path: Path) -> str:
    return str(path.resolve())


def _escape_sh_path(path: Path) -> str:
    return str(path.resolve())


def write_windows_uninstall(
    install_dir: Path,
    data_dir: Path,
    model_dir: Path,
) -> None:
    app_dir = _escape_windows_path(install_dir)
    data = _escape_windows_path(data_dir)
    model = _escape_windows_path(model_dir)
    script = install_dir / "uninstall-prof-finder.bat"
    script.write_text(
        f"""@echo off
setlocal

set "APP_DIR={app_dir}"
set "DATA_DIR={data}"
set "MODEL_DIR={model}"

echo This will permanently delete Prof-Finder, its user data, and the embedding model.
echo.
echo App folder:
echo   %APP_DIR%
echo Data folder:
echo   %DATA_DIR%
echo Model folder:
echo   %MODEL_DIR%
echo.
echo Close all running Prof-Finder windows before continuing.
set /p CONFIRM=Type DELETE to continue:
if not "%CONFIRM%"=="DELETE" (
  echo Cancelled.
  exit /b 1
)

if not exist "%APP_DIR%\\Prof-Finder.exe" (
  echo Refusing to remove app folder because Prof-Finder.exe was not found in:
  echo   %APP_DIR%
  exit /b 1
)

if "%DATA_DIR%"=="" (
  echo Refusing to remove an empty data directory path.
  exit /b 1
)
if /I "%DATA_DIR%"=="%USERPROFILE%" (
  echo Refusing to remove the user profile directory.
  exit /b 1
)
if "%DATA_DIR:~1%"==":\\" (
  echo Refusing to remove a drive root.
  exit /b 1
)

if "%MODEL_DIR%"=="" (
  echo Refusing to remove an empty model directory path.
  exit /b 1
)
if /I "%MODEL_DIR%"=="%USERPROFILE%" (
  echo Refusing to remove the user profile directory.
  exit /b 1
)
if "%MODEL_DIR:~1%"==":\\" (
  echo Refusing to remove a drive root.
  exit /b 1
)

if exist "%DATA_DIR%" (
  rmdir /s /q "%DATA_DIR%"
)

if exist "%MODEL_DIR%" (
  rmdir /s /q "%MODEL_DIR%"
)

echo Removing portable app folder...
cd /d "%TEMP%"
set "CLEANUP=%TEMP%\\prof-finder-uninstall-%RANDOM%-%RANDOM%.cmd"
> "%CLEANUP%" echo @echo off
>> "%CLEANUP%" echo timeout /t 2 /nobreak ^>nul
>> "%CLEANUP%" echo rmdir /s /q "%APP_DIR%"
>> "%CLEANUP%" echo del "%%~f0"
start "" /b cmd /c ""%CLEANUP%""
echo Uninstall scheduled. You can close this window.
endlocal
""",
        encoding="utf-8",
        newline="\r\n",
    )


def write_unix_uninstall(
    install_dir: Path,
    data_dir: Path,
    model_dir: Path,
) -> None:
    app_dir = _escape_sh_path(install_dir)
    data = _escape_sh_path(data_dir)
    model = _escape_sh_path(model_dir)
    script = install_dir / "uninstall-prof-finder.sh"
    script.write_text(
        f"""#!/usr/bin/env sh
set -eu

APP_DIR='{app_dir}'
DATA_DIR='{data}'
MODEL_DIR='{model}'

printf '%s\\n\\n' 'This will permanently delete Prof-Finder, its user data, and the embedding model.'
printf 'App folder:\\n  %s\\n' "$APP_DIR"
printf 'Data folder:\\n  %s\\n' "$DATA_DIR"
printf 'Model folder:\\n  %s\\n\\n' "$MODEL_DIR"
printf '%s\\n' 'Close all running Prof-Finder windows before continuing.'
printf '%s' 'Type DELETE to continue: '
IFS= read -r CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
  printf '%s\\n' 'Cancelled.'
  exit 1
fi

if [ ! -f "${{APP_DIR}}/Prof-Finder" ]; then
  printf '%s\\n' "Refusing to remove app folder because Prof-Finder was not found in:"
  printf '  %s\\n' "$APP_DIR"
  exit 1
fi

for DIR in "$DATA_DIR" "$MODEL_DIR"; do
  case "$DIR" in
    ""|"/"|"$HOME"|"$HOME/")
      printf '%s\\n' "Refusing to remove unsafe directory:"
      printf '  %s\\n' "$DIR"
      exit 1
      ;;
  esac
done

if [ -d "$DATA_DIR" ]; then
  rm -rf -- "$DATA_DIR"
fi

if [ -d "$MODEL_DIR" ]; then
  rm -rf -- "$MODEL_DIR"
fi

cd /
rm -rf -- "$APP_DIR"
printf '%s\\n' 'Prof-Finder portable app, user data, and model have been removed.'
""",
        encoding="utf-8",
    )
    script.chmod(0o755)


def write_uninstall_scripts(
    install_dir: Path,
    data_dir: Path,
    model_dir: Path,
) -> None:
    """Write platform-specific uninstall scripts with embedded paths."""
    if sys.platform == "win32":
        write_windows_uninstall(install_dir, data_dir, model_dir)
    else:
        write_unix_uninstall(install_dir, data_dir, model_dir)


def write_placeholder_uninstall(install_dir: Path, platform_tag: str) -> None:
    """Write initial uninstall scripts before first-run setup completes."""
    from ..runtime import default_suggested_data_dir, model_dir_for_data_root

    data_dir = default_suggested_data_dir()
    model_dir = model_dir_for_data_root(data_dir)
    if platform_tag.startswith("windows-"):
        write_windows_uninstall(install_dir, data_dir, model_dir)
    else:
        write_unix_uninstall(install_dir, data_dir, model_dir)
