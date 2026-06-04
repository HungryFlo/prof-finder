## MODIFIED Requirements

### Requirement: Professor name locales

The system SHALL store optional explicit `name_locales` on `Professor` (`zh` / `en`) for letters. Trusted external sources MAY auto-fill empty locale slots when crawl or high-confidence match succeeds; user-provided locale values SHALL NOT be overwritten.

#### Scenario: User sets bilingual display names
- **WHEN** a user edits a professor and provides `name_locales` for `zh` and/or `en`
- **THEN** the system persists those values on the professor record
- **AND** letter generation may use the locale appropriate to the selected letter language

#### Scenario: Auto-fill from school crawler
- **WHEN** a professor is created by a university crawler with a Chinese `name`
- **THEN** the system writes that name into `name_locales.zh` if `zh` was empty
- **AND** does not derive English from pinyin

#### Scenario: Auto-fill English from Scholar or DBLP
- **WHEN** Scholar or DBLP crawl or confident DBLP match provides an English author name
- **THEN** the system writes it into `name_locales.en` if `en` was empty
- **AND** does not write `en` when DBLP match status is `ambiguous`

#### Scenario: Scholar refresh preserves Chinese locale
- **WHEN** batch Scholar refresh updates `name` to an English Scholar name
- **AND** the previous `name` contained CJK characters
- **THEN** the system copies the previous name into `name_locales.zh` if `zh` was empty

## ADDED Requirements

### Requirement: No pinyin name locale inference

The system SHALL NOT populate `name_locales.en` from pinyin or `generate_search_terms` output.

#### Scenario: Pinyin search terms are not persisted
- **WHEN** DBLP or Scholar matching generates pinyin search terms from a Chinese name
- **THEN** those terms are used only for search
- **AND** are not written to `name_locales`

### Requirement: Professor list omits name locales

The professor list API and list UI SHALL continue to expose only the primary `name` field, not `name_locales`.

#### Scenario: List response unchanged
- **WHEN** a client requests the paginated professor list
- **THEN** each item includes `name` as today
- **AND** does not require `name_locales` on list items
