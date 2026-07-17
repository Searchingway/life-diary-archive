# Mobile Client Requirements

## Requirement: Local-first records

The mobile client SHALL store diary, footprint, and order records locally without requiring an account or network connection.

### Scenario: Offline save

- **WHEN** the user saves any supported record while offline
- **THEN** the record is persisted in the local SQLite database

## Requirement: Portable archive

The mobile client SHALL export text metadata and referenced images in one ZIP archive and SHALL create a safety backup before destructive restore.

### Scenario: Restore archive

- **WHEN** the user confirms restoring a valid archive
- **THEN** the current state is backed up before the archive replaces active records

## Requirement: Order status priority

The order list SHALL prioritize accepted unfinished work, then accepted completed work awaiting payment, and SHALL sort records within each status by date descending.
