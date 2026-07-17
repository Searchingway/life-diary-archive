# Proposal: Expo mobile rewrite

## Why

The existing Qt Android client is difficult to use and expensive to evolve. The project needs a mobile-native interface that remains local-first and preserves the established archive contract.

## What Changes

- Add an Expo SDK 56 / React Native / TypeScript Android client under `mobile/`.
- Store active mobile records in SQLite while preserving the `Diary/entries`, `Diary/footprints`, and `Diary/info_memos` ZIP structure.
- Support diary images, footprint visits, order statuses, backup/restore, and legacy Qt data import.
- Keep Android package identity and release signing compatible with the existing application.

## Impact

The old Qt source remains untouched. The new APK can replace the old package only when signed by the same local release key. Restore operations replace current records after first creating a safety backup.
