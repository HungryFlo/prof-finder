## ADDED Requirements

### Requirement: Semantic Similarity Scoring
The system SHALL compute match scores between a user profile and a professor using
cosine similarity of sentence-transformer embeddings (allenai-specter model), producing
a float score in the range 0–100 that reflects semantic relatedness rather than exact
keyword overlap.

#### Scenario: Semantically related profile matches professor
- **WHEN** a profile lists skills "NLP, transformer models" and a professor's research
  interests include "natural language processing, large language models"
- **THEN** the match score SHALL be above 50 even though no exact keywords overlap

#### Scenario: Unrelated profile returns low score
- **WHEN** a profile lists only "robotics, control systems" and a professor works only
  on "database query optimisation"
- **THEN** the match score SHALL be below 40

#### Scenario: Score range is always valid
- **WHEN** any profile is matched against any professor
- **THEN** the returned score SHALL be in the range [0, 100] inclusive

### Requirement: Professor Embedding Caching
The system SHALL compute and persist a vector embedding for each professor in the
database so that repeated match runs do not re-encode professor data.

#### Scenario: Embedding computed on first match run
- **WHEN** a professor has no stored embedding and a match task is executed
- **THEN** the system SHALL compute the professor's embedding using allenai-specter
  and persist it to the `professors.embedding` column before scoring

#### Scenario: Cached embedding reused on subsequent runs
- **WHEN** a professor already has a stored embedding and a new match task is executed
- **THEN** the system SHALL use the stored embedding without calling the model again

### Requirement: Batch Encoding of Uncached Professors
The system SHALL batch-encode all professors lacking a stored embedding in a single
model call rather than encoding them one at a time, to minimise model overhead.

#### Scenario: Multiple professors encoded efficiently
- **WHEN** N professors have no stored embedding (N > 1)
- **THEN** the system SHALL encode all N professors in a single `model.encode()` call
  with `batch_size=32`, not N separate calls

### Requirement: Match Reasons in Semantic Mode
The system SHALL return human-readable match reasons alongside the semantic score,
indicating the similarity level and the professor's top research interests.

#### Scenario: Reasons include similarity level label
- **WHEN** cosine similarity is above 0.6
- **THEN** reasons SHALL include "语义高度匹配" and list up to 3 research interests

#### Scenario: Reasons include similarity level label for moderate match
- **WHEN** cosine similarity is between 0.3 and 0.6
- **THEN** reasons SHALL include "语义较好匹配" and list up to 3 research interests

#### Scenario: Reasons always include raw similarity value
- **WHEN** any match is computed
- **THEN** reasons SHALL include a string of the form "语义相似度: X.XX"
