## Context
Prof-Finder is a local-first FastAPI and Vue application backed by SQLite. The development workflow uses separate backend and frontend processes, but a non-technical user needs a single downloadable artifact that runs locally and opens in a browser.

## Goals / Non-Goals
- Goals: provide platform-specific portable archives; avoid requiring Python/Node installation for end users; keep the app browser-based; keep user data outside the extracted package; automate release artifact creation.
- Non-Goals: native desktop shell, installers, automatic updates, code signing/notarization, cloud hosting.

## Decisions
- Decision: use FastAPI to serve the built frontend in production mode.
  Alternatives considered: ship a separate frontend server or embed a desktop WebView. A single local HTTP server is simpler and matches the existing browser-based app.
- Decision: use PyInstaller for the first portable executable.
  Alternatives considered: Nuitka and installer frameworks. PyInstaller is adequate for a first portable archive and easier to integrate with the current Poetry project.
- Decision: store packaged runtime state in per-user application data directories.
  Alternatives considered: write next to the executable. Extracted app directories can be read-only or accidentally deleted, so user data must be separate.

## Risks / Trade-offs
- PyInstaller hidden imports and data files may need adjustment as dependencies change.
- macOS Gatekeeper and Windows SmartScreen may warn on unsigned binaries until signing is added.
- Google Scholar scraping and LLM features still require network access and user-provided API credentials.

## Migration Plan
Existing development behavior remains unchanged. Packaged mode is opt-in through the launcher/build artifacts and uses a package-specific environment flag to switch runtime paths.
