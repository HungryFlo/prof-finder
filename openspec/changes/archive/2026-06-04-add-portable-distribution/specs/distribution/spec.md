## ADDED Requirements
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
The system SHALL store packaged runtime state in a per-user data directory.

#### Scenario: Runtime data location
- **WHEN** the application runs in packaged mode
- **THEN** SQLite databases, queue state, logs, and runtime configuration are stored under the user's application data directory
- **AND** they are not stored in the extracted package directory by default.

#### Scenario: Development behavior
- **WHEN** the application runs in development mode
- **THEN** existing environment variables and `.env` behavior continue to determine runtime paths.

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
- **WHEN** a user runs the platform-specific uninstall script
- **AND** types `DELETE` at the confirmation prompt
- **THEN** the script deletes the Prof-Finder user data directory
- **AND** attempts to remove the extracted portable application directory.

#### Scenario: User cancels uninstall
- **WHEN** a user runs the uninstall script
- **AND** does not type `DELETE`
- **THEN** the script exits without deleting user data or application files.
