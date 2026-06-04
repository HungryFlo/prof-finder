# distribution Specification

## Purpose
TBD - created by archiving change add-portable-distribution. Update Purpose after archive.
## Requirements
### Requirement: Portable Local Application
The system SHALL provide a portable local application distribution for each supported desktop platform.

#### Scenario: User launches portable app
- **WHEN** a user downloads and extracts the platform-specific portable package
- **AND** starts the Prof-Finder executable
- **THEN** the application starts a local backend service
- **AND** opens the system browser to the local web interface
- **AND** does not require the user to install Python, Node.js, Poetry, or npm.

#### Scenario: Browser based UI
- **WHEN** the packaged application is running
- **THEN** the Vue frontend is served by the local backend
- **AND** API calls use the same local origin under `/api`
- **AND** refreshing frontend routes does not return a 404.

### Requirement: Packaged Runtime Data
The system SHALL store packaged runtime state in user-selected directories configured on first launch.

#### Scenario: Runtime data location
- **WHEN** the application runs in packaged mode and first-run setup has completed
- **THEN** SQLite databases, queue state, logs, and runtime configuration are stored under the configured data directory
- **AND** the embedding model is stored under `{data_dir}/models/qwen3-embedding-0.6b`
- **AND** the chosen paths are recorded in `install.json` beside the portable executable.

#### Scenario: First-run setup required
- **WHEN** the application runs in packaged mode and `install.json` does not exist
- **THEN** the user is guided through a built-in setup page to choose a data root directory
- **AND** the database and background workers are not initialized until setup completes
- **AND** completing setup rewrites the portable uninstall scripts with the chosen paths.

#### Scenario: Development behavior
- **WHEN** the application runs in development mode
- **THEN** existing environment variables and `.env` behavior continue to determine runtime paths
- **AND** first-run setup is not required.

### Requirement: Automated Portable Release Builds
The system SHALL provide release automation for portable artifacts.

#### Scenario: Tag release
- **WHEN** a GitHub release tag workflow runs
- **THEN** Windows, macOS, and Linux jobs build the frontend and packaged executable
- **AND** upload platform-specific portable archives as release artifacts.

#### Scenario: Artifact contents
- **WHEN** a portable archive is extracted
- **THEN** it contains the Prof-Finder launcher executable, frontend assets, backend runtime resources, user-facing startup documentation, and a platform-specific uninstall script.

### Requirement: Portable Uninstall Script
The system SHALL include a destructive uninstall script in each portable package.

#### Scenario: User confirms uninstall
- **WHEN** a user runs the platform-specific uninstall script after first-run setup
- **AND** types `DELETE` at the confirmation prompt
- **THEN** the script deletes the configured user data directory
- **AND** deletes the configured embedding model directory
- **AND** attempts to remove the extracted portable application directory.

#### Scenario: User cancels uninstall
- **WHEN** a user runs the uninstall script
- **AND** does not type `DELETE`
- **THEN** the script exits without deleting user data, model files, or application files.

