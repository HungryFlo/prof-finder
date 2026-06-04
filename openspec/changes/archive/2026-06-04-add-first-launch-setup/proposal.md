# Change: Add First-Launch Storage Setup

## Why
Portable users often need to store large databases and embedding models on a non-system drive. A built-in first-run wizard lets them choose a data root before the app initializes, and keeps uninstall scripts aligned with that choice.

## What Changes
- Add packaged first-run `/setup` UI and `/api/setup` endpoints.
- Persist `install.json` beside the executable with `data_dir` and `model_dir`.
- Rewrite uninstall scripts when setup completes (always delete data and model paths).
- Skip database initialization until setup is complete.

## Impact
- Affected specs: distribution
- Affected code: runtime paths, launcher, setup API, frontend router, build_portable uninstall generation
