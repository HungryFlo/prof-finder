## MODIFIED Requirements

### Requirement: Semantic Similarity Scoring
The system SHALL compute match scores between a user profile and a professor using
cosine similarity of sentence-transformer embeddings (allenai-specter model), producing
a float score in the range 0–100 that reflects semantic relatedness rather than exact
keyword overlap. When generated student or professor profile fields are available, the
system SHALL use them as the primary text for embedding construction.

#### Scenario: Semantically related profile matches professor
- **WHEN** a profile lists skills "NLP, transformer models" and a professor's research
  interests include "natural language processing, large language models"
- **THEN** the match score SHALL be above 50 even though no exact keywords overlap

#### Scenario: Generated profiles improve matching text
- **WHEN** a student profile has generated academic profile content
- **AND** a professor has generated research profile content
- **THEN** the embedding text SHALL prioritize those generated profile fields
- **AND** include existing resume and professor fields as supporting signals

#### Scenario: Unrelated profile returns low score
- **WHEN** a profile lists only "robotics, control systems" and a professor works only
  on "database query optimisation"
- **THEN** the match score SHALL be below 40

#### Scenario: Score range is always valid
- **WHEN** any profile is matched against any professor
- **THEN** the returned score SHALL be in the range [0, 100] inclusive

#### Scenario: Auto-enriched professor text
- **WHEN** a professor was recently added or refreshed through the system's default import flows
- **THEN** the system SHALL have attempted to populate English `paper_summaries` (when Scholar-backed publications exist) and a research profile before the user initiates matching
- **AND** semantic scoring SHALL use those fields when present according to existing embedding construction rules
