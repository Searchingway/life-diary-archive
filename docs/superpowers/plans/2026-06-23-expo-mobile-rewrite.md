# Expo Mobile Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Qt/QML phone client with a signed Expo/React Native Android app that supports the core local-first diary workflow.

**Architecture:** Add an independent `mobile/` Expo SDK 56 application while leaving `android/LifeDiaryMobile/` unchanged as a rollback reference. The app stores normalized records in persistent SQLite, stores image files in the app document directory, and imports/exports a ZIP package compatible with the existing `Diary/` directory convention.

**Tech Stack:** Expo SDK 56, React Native, Expo Router, TypeScript, expo-sqlite, expo-file-system, expo-image-picker, expo-document-picker, expo-sharing, JSZip, Vitest, Android Gradle.

## Global Constraints

- Keep `diary_v2.0/`, its real data, and `android/LifeDiaryMobile/` unchanged.
- Use Android package `com.localfirst.lifediary`, version code greater than the Qt app's `2`, and the existing local release keystore only at build time.
- Never commit keystores, passwords, generated native build folders, APKs, user data, or `node_modules`.
- Core scope is diary, footprints, order memos, images, backup export/import, and legacy `Diary/` import.
- Deletes are soft deletes; destructive import requires confirmation and creates a backup first.
- Draft save failures retain current screen input.

---

### Task 1: Expo 56 application scaffold and shared design system

**Files:**
- Create: `mobile/package.json`
- Create: `mobile/app.json`
- Create: `mobile/app/_layout.tsx`
- Create: `mobile/app/(tabs)/_layout.tsx`
- Create: `mobile/src/theme.ts`
- Create: `mobile/src/components/Screen.tsx`
- Create: `mobile/src/components/EmptyState.tsx`
- Create: `mobile/src/components/StatusBanner.tsx`

**Interfaces:**
- Produces a five-tab app shell for Home, Diary, Footprints, Orders, and Data.
- Produces reusable restrained green/neutral mobile styling.

- [ ] Scaffold Expo SDK 56 with TypeScript and Expo Router.
- [ ] Configure app name `人生档案`, package `com.localfirst.lifediary`, version `2.1.0`, versionCode `3`, portrait-friendly adaptive icon, and light theme.
- [ ] Add shared screen, toolbar, form, list-row, empty-state, and status components.
- [ ] Run `npm run typecheck` and `npm test`.

### Task 2: SQLite repository, models, and compatibility serializers

**Files:**
- Create: `mobile/src/db/schema.ts`
- Create: `mobile/src/db/database.ts`
- Create: `mobile/src/db/repository.ts`
- Create: `mobile/src/domain/models.ts`
- Create: `mobile/src/domain/orderSort.ts`
- Create: `mobile/src/compat/archive.ts`
- Create: `mobile/src/__tests__/repository.test.ts`
- Create: `mobile/src/__tests__/orderSort.test.ts`
- Create: `mobile/src/__tests__/archive.test.ts`

**Interfaces:**
- Produces `initializeDatabase()`, diary/footprint/order CRUD repositories, soft delete, search, counts, and archive conversion functions.
- Stores module-specific fields as JSON while indexing title, date, status, and updated time.

- [ ] Write failing tests for schema initialization, CRUD, soft delete, search, status sorting, and archive round-trip.
- [ ] Implement SQLite migrations and repositories using parameterized queries and transactions.
- [ ] Implement existing order priority: active accepted work first, accepted unpaid next, then quote/completed/paid/abandoned, each newest first.
- [ ] Implement pure archive serializers/parsers for `entries/`, `footprints/`, and `info_memos/`.
- [ ] Run `npm test`.

### Task 3: Diary screen with safe drafts and images

**Files:**
- Create: `mobile/app/(tabs)/diary.tsx`
- Create: `mobile/src/features/diary/DiaryEditor.tsx`
- Create: `mobile/src/features/diary/DiaryList.tsx`
- Create: `mobile/src/features/images/ImageStrip.tsx`
- Create: `mobile/src/services/images.ts`

**Interfaces:**
- Consumes diary repository and image service.
- Supports search, create, edit, manual save, three-second autosave, soft delete, image pick, caption, reorder, and remove.

- [ ] Implement list/loading/empty/error states without clearing the last successful list.
- [ ] Implement draft lifecycle and three-second autosave with retained input on failure.
- [ ] Copy selected images into the app document directory without modifying originals.
- [ ] Add confirmed soft delete and image removal.
- [ ] Run typecheck, tests, and Expo Android export.

### Task 4: Footprints and order memo screens

**Files:**
- Create: `mobile/app/(tabs)/footprints.tsx`
- Create: `mobile/app/(tabs)/orders.tsx`
- Create: `mobile/src/features/footprints/FootprintEditor.tsx`
- Create: `mobile/src/features/orders/OrderEditor.tsx`

**Interfaces:**
- Consumes footprint/order repositories and shared image service.
- Footprints support places, visits, thoughts, and visit images.
- Orders support all six statuses and desktop-compatible fields.

- [ ] Implement place list, place editing, nested visits, visit thoughts, and images.
- [ ] Implement order list grouped by business priority and sorted newest-first within each status.
- [ ] Implement customer, intermediary, executor, dates, duration, price, deposit, final payment, deliverables, and notes.
- [ ] Add save-failure retention and confirmed soft deletion.
- [ ] Run typecheck, tests, and Expo Android export.

### Task 5: Data dashboard, ZIP backup, restore, and Qt legacy import

**Files:**
- Create: `mobile/app/(tabs)/index.tsx`
- Create: `mobile/app/(tabs)/data.tsx`
- Create: `mobile/src/services/backup.ts`
- Create: `mobile/src/services/legacyImport.ts`
- Create: `mobile/src/__tests__/legacyImport.test.ts`

**Interfaces:**
- Produces module counts, ZIP export/share, document-picker import, pre-import safety backup, and idempotent import.
- Reads legacy Qt `Diary/` folders from the same package document area when available.

- [ ] Implement home counts and recent records.
- [ ] Export `manifest.json` plus `Diary/entries`, `Diary/footprints`, and `Diary/info_memos` to ZIP and open the system share sheet.
- [ ] Import ZIP only after confirmation and a successful safety backup; use transactions and preserve current data on failure.
- [ ] Detect and import legacy Qt file records without deleting or moving source files.
- [ ] Run typecheck, tests, and archive round-trip tests.

### Task 6: Android release build, signing, verification, and handoff

**Files:**
- Create: `mobile/scripts/build-android-release.ps1`
- Create: `mobile/README.md`
- Modify: `.gitignore`
- Modify: `README.md`
- Modify: `docs/技术选型.md`
- Create: `docs/release-notes/mobile-expo-2.1.0.md`

**Interfaces:**
- Produces a release APK signed with the existing local keystore.
- Copies the verified APK to the Windows desktop without committing it.

- [ ] Generate native Android files with `npx expo prebuild --platform android --clean`.
- [ ] Configure release signing from environment variables/local untracked properties and build `assembleRelease`.
- [ ] Verify package, version, certificate, and APK integrity with `apkanalyzer`/`aapt` and `apksigner`.
- [ ] Run full mobile tests, typecheck, Expo export, Android release build, and existing repo regression tests.
- [ ] Copy the signed APK to `C:\Users\hp\Desktop\人生档案-Expo-2.1.0-release-signed.apk`.
- [ ] Confirm generated native folders, APKs, keystore, and passwords are not tracked.
