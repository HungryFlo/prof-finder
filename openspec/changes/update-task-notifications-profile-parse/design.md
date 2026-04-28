## Context
The app already has a shared in-memory task registry, SSE progress endpoint, and frontend task panel. Profile upload is the outlier: the web UI waits for parsing to finish, then opens a confirmation modal before saving.

## Goals / Non-Goals
- Goals: make task completion visible through side notifications, keep the task panel useful as a status history, and move web profile parsing into the existing background task pipeline.
- Goals: automatically save parsed web uploads without replacing the current active profile unless no profile is active.
- Non-Goals: persist task state across backend restarts, redesign the task system, or change the CLI confirmation flow.

## Decisions
- Decision: use a new `profile-parse` task type and existing SSE complete event results for the created profile summary.
- Decision: keep validation of uploaded file extension, encoding, and empty content in the request handler before creating the task so invalid uploads fail immediately.
- Decision: keep UI notification rendering outside the Pinia store; the store will expose task events and a small host component will call Naive UI notifications.
- Alternatives considered: saving a draft profile before parsing, or adding a separate parsed-draft endpoint. These add persistence and cleanup requirements not needed for the requested automatic-save flow.

## Risks / Trade-offs
- In-memory task results are lost on backend restart, matching the existing task infrastructure. Saved profiles remain durable once the task succeeds.
- Since parsed profiles are saved automatically, users must edit the profile after creation if parser output needs correction.

## Migration Plan
No data migration is required. Existing profiles and existing task types continue to work unchanged.
