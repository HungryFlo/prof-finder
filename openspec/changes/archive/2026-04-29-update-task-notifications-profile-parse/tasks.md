## 1. OpenSpec
- [x] 1.1 Add task-panel and resume-parser spec deltas
- [x] 1.2 Validate the change with strict OpenSpec validation

## 2. Backend
- [x] 2.1 Add `profile-parse` task execution that parses and saves uploaded resumes
- [x] 2.2 Change `POST /api/profiles/upload` to return `TaskStartResponse`
- [x] 2.3 Add or update backend tests for async profile upload behavior

## 3. Frontend
- [x] 3.1 Add task completion/failure notification handling
- [x] 3.2 Improve task panel grouping and status labels
- [x] 3.3 Change profile upload UI to start a background task and remove the parse confirmation modal

## 4. Verification
- [x] 4.1 Run OpenSpec validation
- [x] 4.2 Run frontend type checks or build
- [x] 4.3 Run backend profile/task tests
