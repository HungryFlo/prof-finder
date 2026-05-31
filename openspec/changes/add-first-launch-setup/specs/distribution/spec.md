## MODIFIED Requirements

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
