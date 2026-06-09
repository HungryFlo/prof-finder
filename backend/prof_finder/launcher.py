"""Portable local application launcher for Prof-Finder."""

from __future__ import annotations

import argparse
import logging
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import uvicorn

from prof_finder.runtime import (
    PACKAGE_ENV,
    apply_install_config,
    install_dir,
    is_configured,
    is_packaged,
    logs_dir,
    user_data_dir,
)


def _available_port(host: str, preferred_port: int) -> int:
    """Return the preferred port if available, otherwise an OS-assigned port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, preferred_port))
            return preferred_port
        except OSError:
            pass

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _wait_for_health(url: str, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.25)

    raise RuntimeError(f"Prof-Finder server did not become ready: {last_error}")


def run(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    """Start the local server and optionally open the system browser."""
    os.environ.setdefault(PACKAGE_ENV, "1")
    if is_packaged():
        os.chdir(install_dir())
    apply_install_config()

    log_file = None
    if not is_packaged() or is_configured():
        data_dir = user_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir() / "prof-finder.log"
        logging.basicConfig(
            filename=log_file,
            level=getattr(
                logging, os.getenv("PROF_FINDER_LOG_LEVEL", "INFO").upper(), logging.INFO
            ),
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )

    selected_port = _available_port(host, port)

    # Import after packaged-mode environment is set so settings use user data paths.
    from prof_finder.api.main import app

    config = uvicorn.Config(
        app,
        host=host,
        port=selected_port,
        log_level=os.getenv("PROF_FINDER_LOG_LEVEL", "info"),
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="prof-finder-server", daemon=True)
    thread.start()

    base_url = f"http://{host}:{selected_port}"
    _wait_for_health(f"{base_url}/api/health", timeout_seconds=30)

    print(f"Prof-Finder is running at {base_url}")
    if is_packaged() and not is_configured():
        print("First-run setup required. Opening setup wizard...")
        if open_browser:
            webbrowser.open(f"{base_url}/setup")
    else:
        print(f"User data directory: {user_data_dir()}")
        if log_file is not None:
            print(f"Log file: {log_file}")
        if open_browser:
            webbrowser.open(base_url)

    try:
        while thread.is_alive():
            thread.join(timeout=0.5)
    except KeyboardInterrupt:
        print("Stopping Prof-Finder...")
        server.should_exit = True
        thread.join(timeout=10)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the Prof-Finder local application.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.getenv("PROF_FINDER_PORT", "8000")))
    parser.add_argument("--no-browser", action="store_true", help="Start without opening a browser.")
    args = parser.parse_args(argv)

    try:
        run(host=args.host, port=args.port, open_browser=not args.no_browser)
        return 0
    except Exception as exc:
        print(f"Failed to start Prof-Finder: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
