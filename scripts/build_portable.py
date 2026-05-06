"""Build a portable Prof-Finder archive for the current platform."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
PYINSTALLER_DIST = REPO_ROOT / "build" / "pyinstaller-dist"
PYINSTALLER_WORK = REPO_ROOT / "build" / "pyinstaller-work"
PORTABLE_DIST = REPO_ROOT / "dist" / "portable"


def run(command: list[str], cwd: Path = REPO_ROOT) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def npm_command(*args: str) -> list[str]:
    """Return an npm command that works with Windows GitHub runners."""
    executable = "npm.cmd" if sys.platform == "win32" else "npm"
    return [executable, *args]


def normalize_platform_tag() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    arch = {
        "amd64": "x64",
        "x86_64": "x64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, machine)

    os_name = {
        "darwin": "macos",
        "windows": "windows",
        "linux": "linux",
    }.get(system, system)

    return f"{os_name}-{arch}"


def build_frontend(skip_install: bool) -> None:
    if not skip_install:
        run(npm_command("ci"), cwd=FRONTEND_DIR)
    run(npm_command("run", "build"), cwd=FRONTEND_DIR)


def build_executable() -> Path:
    if PYINSTALLER_DIST.exists():
        shutil.rmtree(PYINSTALLER_DIST)
    if PYINSTALLER_WORK.exists():
        shutil.rmtree(PYINSTALLER_WORK)

    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--distpath",
            str(PYINSTALLER_DIST),
            "--workpath",
            str(PYINSTALLER_WORK),
            str(REPO_ROOT / "packaging" / "prof-finder.spec"),
        ]
    )

    executable = PYINSTALLER_DIST / ("Prof-Finder.exe" if sys.platform == "win32" else "Prof-Finder")
    if not executable.exists():
        executable = (
            PYINSTALLER_DIST
            / "Prof-Finder"
            / ("Prof-Finder.exe" if sys.platform == "win32" else "Prof-Finder")
        )
    if not executable.exists():
        raise FileNotFoundError(f"Expected PyInstaller output not found: {executable}")
    return executable


def write_portable_readme(target_dir: Path) -> None:
    (target_dir / "README-PORTABLE.txt").write_text(
        """Prof-Finder Portable

Start:
  - Windows: double-click Prof-Finder.exe
  - macOS/Linux: run ./Prof-Finder

The app starts a local server and opens your system browser.
User data is stored in your OS user data directory, not inside this extracted folder.

Uninstall and remove data:
  - Windows: close Prof-Finder, then run uninstall-prof-finder.bat
  - macOS/Linux: close Prof-Finder, then run ./uninstall-prof-finder.sh

The uninstall script deletes the Prof-Finder user data directory and then removes this
extracted portable app folder. It asks you to type DELETE before doing anything.

Default admin account:
  username: root
  password: root123

On first login, change the default password and configure your DeepSeek API key in Settings.
""",
        encoding="utf-8",
    )


def write_uninstall_script(target_dir: Path, platform_tag: str) -> None:
    """Write a platform-specific destructive uninstall script into the package."""
    if platform_tag.startswith("windows-"):
        script = target_dir / "uninstall-prof-finder.bat"
        script.write_text(
            r"""@echo off
setlocal

set "APP_DIR=%~dp0"
if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"

if defined PROF_FINDER_DATA_DIR (
  set "DATA_DIR=%PROF_FINDER_DATA_DIR%"
) else (
  set "DATA_DIR=%APPDATA%\Prof-Finder"
)

echo This will permanently delete Prof-Finder and its local user data.
echo.
echo App folder:
echo   %APP_DIR%
echo Data folder:
echo   %DATA_DIR%
echo.
echo Close all running Prof-Finder windows before continuing.
set /p CONFIRM=Type DELETE to continue:
if not "%CONFIRM%"=="DELETE" (
  echo Cancelled.
  exit /b 1
)

if not exist "%APP_DIR%\Prof-Finder.exe" (
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
if "%DATA_DIR:~1%"==":\" (
  echo Refusing to remove a drive root.
  exit /b 1
)

if exist "%DATA_DIR%" (
  rmdir /s /q "%DATA_DIR%"
)

echo Removing portable app folder...
cd /d "%TEMP%"
set "CLEANUP=%TEMP%\prof-finder-uninstall-%RANDOM%-%RANDOM%.cmd"
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
        return

    script = target_dir / "uninstall-prof-finder.sh"
    script.write_text(
        r"""#!/usr/bin/env sh
set -eu

APP_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P)

if [ -n "${PROF_FINDER_DATA_DIR:-}" ]; then
  DATA_DIR="${PROF_FINDER_DATA_DIR}"
elif [ "$(uname -s)" = "Darwin" ]; then
  DATA_DIR="${HOME}/Library/Application Support/Prof-Finder"
else
  DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/prof-finder"
fi

printf '%s\n\n' 'This will permanently delete Prof-Finder and its local user data.'
printf 'App folder:\n  %s\n' "$APP_DIR"
printf 'Data folder:\n  %s\n\n' "$DATA_DIR"
printf '%s\n' 'Close all running Prof-Finder windows before continuing.'
printf '%s' 'Type DELETE to continue: '
IFS= read -r CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
  printf '%s\n' 'Cancelled.'
  exit 1
fi

if [ ! -f "${APP_DIR}/Prof-Finder" ]; then
  printf '%s\n' "Refusing to remove app folder because Prof-Finder was not found in:"
  printf '  %s\n' "$APP_DIR"
  exit 1
fi

case "$DATA_DIR" in
  ""|"/"|"$HOME"|"$HOME/")
    printf '%s\n' "Refusing to remove unsafe data directory:"
    printf '  %s\n' "$DATA_DIR"
    exit 1
    ;;
esac

if [ -d "$DATA_DIR" ]; then
  rm -rf -- "$DATA_DIR"
fi

cd /
rm -rf -- "$APP_DIR"
printf '%s\n' 'Prof-Finder portable app and user data have been removed.'
""",
        encoding="utf-8",
    )
    script.chmod(0o755)


def create_archive(executable: Path, platform_tag: str) -> Path:
    package_name = f"Prof-Finder-{platform_tag}"
    staging_dir = PORTABLE_DIST / package_name
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    bundle_dir = executable.parent if executable.parent.parent == PYINSTALLER_DIST else None
    if bundle_dir:
        for item in bundle_dir.iterdir():
            target = staging_dir / item.name
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
    else:
        shutil.copy2(executable, staging_dir / executable.name)
    write_portable_readme(staging_dir)
    write_uninstall_script(staging_dir, platform_tag)

    archive_format = "gztar" if platform_tag.startswith("linux-") else "zip"
    archive_base = PORTABLE_DIST / package_name
    archive_path = shutil.make_archive(str(archive_base), archive_format, staging_dir)
    return Path(archive_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Prof-Finder portable package.")
    parser.add_argument("--platform-tag", default=normalize_platform_tag())
    parser.add_argument("--skip-npm-install", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    args = parser.parse_args()

    if not args.skip_frontend:
        build_frontend(skip_install=args.skip_npm_install)
    elif not (FRONTEND_DIR / "dist" / "index.html").exists():
        raise FileNotFoundError("frontend/dist/index.html is required when --skip-frontend is used")

    executable = build_executable()
    archive_path = create_archive(executable, args.platform_tag)
    print(f"Created portable archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
