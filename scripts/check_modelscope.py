#!/usr/bin/env python3
"""Check whether this machine can reach ModelScope for embedding model download.

Prof-Finder downloads Qwen/Qwen3-Embedding-0.6B from ModelScope (www.modelscope.cn).
Run from terminal:

    python scripts/check_modelscope.py

Exit code 0 = all checks passed; 1 = at least one check failed.
"""

from __future__ import annotations

import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

MODELSCOPE_HOST = "www.modelscope.cn"
MODELSCOPE_BASE = f"https://{MODELSCOPE_HOST}"
MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
TIMEOUT_SEC = 15


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def _proxy_info() -> str:
    keys = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")
    parts = [f"{k}={v}" for k in keys if (v := __import__("os").environ.get(k))]
    return ", ".join(parts) if parts else "(none)"


def check_dns() -> CheckResult:
    try:
        addrs = sorted({ai[4][0] for ai in socket.getaddrinfo(MODELSCOPE_HOST, 443)})
        return CheckResult("DNS", True, f"{MODELSCOPE_HOST} -> {', '.join(addrs)}")
    except socket.gaierror as exc:
        return CheckResult("DNS", False, f"cannot resolve {MODELSCOPE_HOST}: {exc}")


def check_https() -> CheckResult:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((MODELSCOPE_HOST, 443), timeout=TIMEOUT_SEC) as sock:
            with ctx.wrap_socket(sock, server_hostname=MODELSCOPE_HOST) as tls:
                tls.sendall(
                    f"GET / HTTP/1.1\r\nHost: {MODELSCOPE_HOST}\r\nConnection: close\r\n\r\n".encode()
                )
                data = tls.recv(256)
        if b"HTTP/" in data:
            status = data.split(b"\r\n", 1)[0].decode(errors="replace")
            return CheckResult("HTTPS", True, status)
        return CheckResult("HTTPS", False, "connected but no HTTP response")
    except OSError as exc:
        return CheckResult("HTTPS", False, str(exc))


def _http_get(
    url: str,
    headers: Optional[dict[str, str]] = None,
    *,
    max_bytes: Optional[int] = None,
) -> tuple[int, str, dict[str, str]]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
        raw = resp.read() if max_bytes is None else resp.read(max_bytes)
        body = raw.decode("utf-8", errors="replace")
        hdrs = {k: v for k, v in resp.headers.items()}
        return resp.status, body, hdrs


def check_model_api() -> CheckResult:
    url = f"{MODELSCOPE_BASE}/api/v1/models/{MODEL_ID}"
    try:
        status, body, _ = _http_get(url)
        if status != 200:
            return CheckResult("Model API", False, f"HTTP {status} for {url}")
        payload = json.loads(body)
        code = payload.get("Code")
        name = payload.get("Data", {}).get("Name") or payload.get("Data", {}).get("ChineseName")
        if code == 200 and name:
            return CheckResult("Model API", True, f"{MODEL_ID} reachable ({name})")
        return CheckResult("Model API", False, f"unexpected response: Code={code!r}")
    except urllib.error.HTTPError as exc:
        return CheckResult("Model API", False, f"HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        return CheckResult("Model API", False, str(exc.reason))
    except json.JSONDecodeError as exc:
        return CheckResult("Model API", False, f"invalid JSON: {exc}")


def check_file_download() -> CheckResult:
    """Simulate the download path used by modelscope.snapshot_download."""
    file_path = urllib.parse.quote_plus("config.json")
    revision = urllib.parse.quote_plus("master")
    url = (
        f"{MODELSCOPE_BASE}/api/v1/models/{MODEL_ID}/repo"
        f"?Revision={revision}&FilePath={file_path}"
    )
    try:
        status, _, headers = _http_get(url, headers={"Range": "bytes=0-0"}, max_bytes=1)
        if status not in (200, 206):
            return CheckResult("File download", False, f"HTTP {status} for repo file")
        total = headers.get("Content-Range", "").split("/")[-1]
        detail = f"partial download OK (config.json, {total or '?'} bytes total)"
        return CheckResult("File download", True, detail)
    except urllib.error.HTTPError as exc:
        return CheckResult("File download", False, f"HTTP {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        return CheckResult("File download", False, str(exc.reason))


def run_checks() -> list[CheckResult]:
    checks: list[Callable[[], CheckResult]] = [
        check_dns,
        check_https,
        check_model_api,
        check_file_download,
    ]
    return [fn() for fn in checks]


def main() -> int:
    print("ModelScope connectivity check (Prof-Finder embedding model)")
    print(f"Target model: {MODEL_ID}")
    print(f"Proxy env: {_proxy_info()}")
    print()

    results = run_checks()
    for item in results:
        mark = "PASS" if item.ok else "FAIL"
        print(f"[{mark}] {item.name}: {item.detail}")

    passed = sum(r.ok for r in results)
    total = len(results)
    print()
    if passed == total:
        print(f"Result: OK ({passed}/{total}) — this machine should be able to download the embedding model.")
        return 0

    print(f"Result: FAILED ({passed}/{total}) — ModelScope is not fully reachable from this machine.")
    print("Tips:")
    print("  - Ensure general internet access (ModelScope is a domestic CN service; VPN is usually not required).")
    print("  - Check firewall / corporate proxy settings.")
    print("  - If behind a proxy, set HTTPS_PROXY and retry.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
