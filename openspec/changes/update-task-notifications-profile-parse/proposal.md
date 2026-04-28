# Change: Improve task notifications and async profile parsing

## Why
Long-running tasks currently rely on the header task panel for completion awareness, which makes finished work easy to miss when users are focused elsewhere. Resume uploads also block on parsing and require a second confirmation step, which is inconsistent with the rest of the background task workflow.

## What Changes
- Add side notifications for task completion and failure while keeping the existing task panel as the persistent task history.
- Refine the task panel so running, failed, and completed tasks are easier to scan.
- Change web resume upload to start a background `profile-parse` task that parses and saves the profile automatically.
- Preserve the current active profile during automatic save; the new parsed profile becomes active only when the user has no active profile.

## Impact
- Affected specs: `task-panel`, `resume-parser`
- Affected code: `backend/prof_finder/api/routes/profiles.py`, `backend/prof_finder/api/task_manager.py`, `frontend/src/stores/tasks.ts`, `frontend/src/components/TaskPanel.vue`, `frontend/src/views/profile/ProfileListView.vue`
