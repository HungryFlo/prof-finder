## 1. Backend Data Model and Schemas
- [x] 1.1 Add `UserProfile` fields for profile materials metadata, manual inputs, generated academic profile, evidence notes, conflict notes, and generated-at timestamp.
- [x] 1.2 Extend API schemas and TypeScript types to expose the new profile fields.
- [x] 1.3 Add migration or initialization handling for existing SQLite databases.

## 2. Student Profile Generation Pipeline
- [x] 2.1 Add prompt templates for student material analysis and academic profile building.
- [x] 2.2 Implement multi-material intake for `.md`, `.markdown`, `.txt`, `.tex`, and `.latex` uploads.
- [x] 2.3 Support direct manual text fields for research interests, personal statement, research plan, and free-form notes.
- [x] 2.4 Generate and persist the academic profile with source metadata and insufficient-evidence markers.
- [x] 2.5 Reject oversized material bundles with a clear task failure message.

## 3. API and Frontend
- [x] 3.1 Add or extend the Web profile upload endpoint to accept multiple files and manual text in one request.
- [x] 3.2 Update the profile UI to collect multiple materials and show generated profile sections.
- [x] 3.3 Refresh profile lists and detail views after profile generation task completion.

## 4. Downstream Quality
- [x] 4.1 Update semantic matching profile text to prefer generated academic profile fields when present.
- [x] 4.2 Update letter generation context to include concise academic positioning and evidence-backed interests.
- [x] 4.3 Add tests for multi-material intake, manual text priority, conflict notes, older resume-only profiles, and matching text construction.
