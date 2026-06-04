# Change: Add Portable Distribution

## Why
Prof-Finder currently requires users to install Python, Poetry, Node.js, and run separate backend/frontend commands. A portable distribution lets non-technical users download a platform-specific package, launch the app locally, and use it in their browser without installing development tooling.

## What Changes
- Add a packaged local application mode that starts the FastAPI server and opens the system browser.
- Serve the built Vue frontend from the backend in production/package mode.
- Store runtime data and configuration in a per-user data directory instead of the extracted application directory.
- Add repeatable build automation for Windows, macOS, and Linux portable artifacts.

## Impact
- Affected specs: distribution, web-frontend, user-settings
- Affected code: FastAPI app startup/static serving, runtime settings paths, launcher entry point, packaging scripts, GitHub Actions release workflow, README
