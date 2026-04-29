## 1. Backend Data Model and Schemas
- [x] 1.1 Add `Professor` fields for generated research profile, structured analysis, evidence notes, conflict notes, source metadata, and generated-at timestamp.
- [x] 1.2 Extend API schemas and TypeScript types to expose professor research profile fields.
- [x] 1.3 Add migration or initialization handling for existing SQLite databases.

## 2. Professor Research Profile Pipeline
- [x] 2.1 Add prompt templates for professor research analysis and profile building.
- [x] 2.2 Build a source bundle from research interests, publications, paper summaries, source inputs, homepage/source URLs, and manual notes.
- [x] 2.3 Generate structured research analysis with themes, methods, representative works, recent directions, fit signals, evidence, and gaps.
- [x] 2.4 Persist generated research profile fields and clear or refresh cached professor embeddings.
- [x] 2.5 Add a background task path for generating one professor profile and, if needed, batch generation for selected professors.

## 3. API and Frontend
- [x] 3.1 Add API endpoint or professor action to trigger research profile generation.
- [x] 3.2 Update professor detail/edit UI to display generated profile sections, evidence notes, and gaps.
- [x] 3.3 Surface generation status through the existing task panel.

## 4. Downstream Quality
- [x] 4.1 Update semantic matching professor text to prefer generated research profile fields when present.
- [x] 4.2 Update letter generation to cite profile themes, representative works, and student fit signals.
- [x] 4.3 Add tests for source bundle construction, sparse-data gaps, manual note priority, embedding invalidation, matching text construction, and letter context formatting.
