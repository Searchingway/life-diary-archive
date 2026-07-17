# Design

## Architecture

- Expo Router provides five bottom tabs: home, diary, footprints, orders, and data.
- `expo-sqlite` stores normalized record envelopes with module-specific JSON payloads.
- Images are copied into an app-private media directory and referenced by stable file names.
- JSZip exports text metadata and image binaries using the existing archive directory names.

## Data Safety

- Record deletion is soft deletion.
- ZIP restore and legacy import create a current-state safety backup before replacement.
- No network sync or analytics are introduced.
- The app disables Android Auto Backup because image and SQLite consistency is managed by explicit ZIP exports.

## Compatibility

The Android application ID remains `com.localfirst.lifediary`. The migration reader consumes the former `Diary` directory and maps old text metadata into the SQLite record envelope.
