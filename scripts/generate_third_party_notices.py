#!/usr/bin/env python3
"""Regenerate THIRD_PARTY_NOTICES.md (Python prod + frontend prod + models)."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "THIRD_PARTY_NOTICES.md"
FRONTEND_DIR = REPO_ROOT / "frontend"

# pip-licenses sometimes reports UNKNOWN; project-confirmed licenses.
LICENSE_OVERRIDES: dict[str, str] = {
    "huey": "MIT License (see https://github.com/coleifer/huey)",
}

HEADER = """# Third-Party Notices

Prof-Finder is licensed under the [MIT License](LICENSE).

This document lists third-party software **included in or used to build** Prof-Finder
(portable/desktop distribution and source installs). It does not replace the license
text of each component; see the URL or project repository for full terms.

| Section | Scope |
|---------|--------|
| [Python runtime](#python-runtime-dependencies) | Backend and packaged executable (Poetry **main** dependencies and their transitive packages) |
| [Frontend](#frontend-dependencies) | Web UI bundled in releases (`npm` production dependency tree) |
| [Embedding model](#embedding-model-runtime-download) | Downloaded at runtime on first match (not shipped in the git repo) |
| [External services](#external-services-and-data) | APIs and public data sources you connect to at runtime |

**Regenerate this file** (from repo root, with `prof-finder` conda env and `poetry install --with dev`):

```bash
python scripts/generate_third_party_notices.py
```

---

"""


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def normalize_name(name: str) -> str:
    return name.lower().replace("_", "-")


def parse_poetry_main_tree(stdout: str) -> set[str]:
    names: set[str] = set()
    for line in stdout.splitlines():
        if not line.strip() or "RequestsDependencyWarning" in line:
            continue
        cleaned = re.sub(r"^[│\s├└─]+", "", line.strip())
        match = re.match(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*)", cleaned)
        if match:
            names.add(normalize_name(match.group(1)))
    return names


def python_section() -> str:
    tree = run(["poetry", "show", "--only", "main", "--tree"])
    allowed = parse_poetry_main_tree(tree)

    raw = run(["poetry", "run", "pip-licenses", "-f", "json", "-a", "-u"])
    packages = json.loads(raw)

    rows: list[dict[str, str]] = []
    for pkg in packages:
        name = pkg.get("Name", "")
        key = normalize_name(name)
        if key not in allowed:
            continue
        license_name = LICENSE_OVERRIDES.get(key) or pkg.get("License", "UNKNOWN")
        rows.append(
            {
                "name": name,
                "version": pkg.get("Version", ""),
                "license": license_name,
                "author": pkg.get("Author", ""),
                "url": pkg.get("URL", ""),
            }
        )

    rows.sort(key=lambda r: r["name"].lower())

    buf = StringIO()
    buf.write("## Python runtime dependencies\n\n")
    buf.write(
        f"The following **{len(rows)}** Python packages are included in production installs "
        "(Poetry `main` group, including transitive dependencies).\n\n"
    )
    buf.write("| Name | Version | License | Author | URL |\n")
    buf.write("|------|---------|---------|--------|-----|\n")
    for row in rows:
        def esc(value: str) -> str:
            return (value or "").replace("|", "\\|").replace("\n", " ")

        buf.write(
            f"| {esc(row['name'])} | {esc(row['version'])} | {esc(row['license'])} "
            f"| {esc(row['author'])} | {esc(row['url'])} |\n"
        )
    buf.write("\n")
    return buf.getvalue()


def frontend_section() -> str:
    csv_path = REPO_ROOT / "build" / "npm-licenses.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "npx",
            "--yes",
            "license-checker@25.0.1",
            "--production",
            "--csv",
            "--out",
            str(csv_path),
        ],
        cwd=FRONTEND_DIR,
        check=True,
    )

    rows: list[dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            module = (row.get("module name") or row.get("module") or "").strip()
            if not module:
                continue
            rows.append(
                {
                    "module": module,
                    "license": (row.get("license") or "UNKNOWN").strip(),
                    "repository": (row.get("repository") or "").strip(),
                }
            )

    rows.sort(key=lambda r: r["module"].lower())

    buf = StringIO()
    buf.write("## Frontend dependencies\n\n")
    buf.write(
        f"The web UI is built with Vite/Vue. Production bundles include **{len(rows)}** "
        "npm packages (direct and transitive).\n\n"
    )
    buf.write("| Module | License | Repository |\n")
    buf.write("|--------|---------|------------|\n")
    for row in rows:
        def esc(value: str) -> str:
            return (value or "").replace("|", "\\|").replace("\n", " ")

        buf.write(
            f"| {esc(row['module'])} | {esc(row['license'])} | {esc(row['repository'])} |\n"
        )
    buf.write("\n")
    return buf.getvalue()


def static_sections() -> str:
    return """## Embedding model (runtime download)

On first semantic match, Prof-Finder may download an embedding model from ModelScope/Hugging Face:

| Component | License | Source |
|-----------|---------|--------|
| Qwen/Qwen3-Embedding-0.6B | Apache License 2.0 | https://huggingface.co/Qwen/Qwen3-Embedding-0.6B |

Model weights are stored under the user-chosen data directory (`models/`). They are **not** committed to this repository.

## External services and data

These are accessed at runtime under your own account or network; terms are governed by each provider:

| Service | Use in Prof-Finder |
|---------|-------------------|
| [DeepSeek API](https://platform.deepseek.com) | LLM features (resume parsing, profiles, letters, chat) — user-supplied API key |
| [arXiv API](https://arxiv.org/help/api) | Paper metadata for source inputs |
| [Google Scholar](https://scholar.google.com) / [DBLP](https://dblp.org) | Professor and publication metadata (public web/API) |
| [ModelScope](https://www.modelscope.cn) | Optional model download mirror |

"""


def main() -> int:
    parts = [HEADER, python_section(), frontend_section(), static_sections()]
    OUTPUT.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or exc.stdout or str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
