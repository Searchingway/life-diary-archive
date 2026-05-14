## MODIFIED Requirements

### Requirement: Export diary entries sorted by date

The export system SHALL sort diary entries in descending date order when generating Word and PDF documents.

#### Scenario: Word export with multiple entries in descending date order

- **WHEN** user exports multiple diary entries to Word format
- **THEN** the entries SHALL appear in descending date order (newest first)

#### Scenario: PDF export with multiple entries in descending date order

- **WHEN** user exports multiple diary entries to PDF format
- **THEN** the entries SHALL appear in descending date order (newest first)

#### Scenario: Export date range dialog displays correct sort hint

- **WHEN** user opens the export date range dialog
- **THEN** the hint text SHALL indicate entries are sorted newest-first
