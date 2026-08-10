# Life Diary Sync Protocol V1

Desktop is the canonical source of truth. Mobile is a working copy. This protocol deliberately provides a staged import into Desktop followed by a Desktop Canonical ZIP; V1 does not implement mobile receipt or any bidirectional merge algorithm.

## Manifest

Every V1 archive contains `manifest.json`:

```json
{
  "app": "LifeDiary",
  "protocol_version": 1,
  "package_role": "mobile_snapshot",
  "source_platform": "mobile",
  "created_at": "2026-08-10T00:00:00+08:00",
  "schema_versions": {"plans": 2}
}
```

Desktop Canonical ZIP changes only `package_role` to `desktop_canonical` and `source_platform` to `desktop`.  Existing Expo backup archives using `format: life-diary-archive` and `version: 1` are accepted as legacy mobile snapshots, but Desktop always produces the V1 manifest above.

## Scope and safety

Only `entries`, `footprints`, `plans`, and `info_memos` are synchronised. Desktop-only modules are never included in a canonical ZIP and are never deleted or modified by sync. ZIP member paths must be relative, unique, and free from traversal. Import runs preflight, creates a safety backup, stages all results, requires every conflict to be resolved, and only then commits.

## Plan V2

Plans use `schema_version: 2`; the canonical shared fixture is `shared/sync/fixtures/plan_v2_full.json`. Readers migrate V1 aliases losslessly: `deadline` to `due_date`, `startDate` to `start_date`, `task.date` to `task.scheduled_date`, `暂停` to `已暂停`, and `普通` to `中`.

## Entry conflict policy

`updated_at` is display-only. Same-ID entries are `unchanged` only when normalised date/title/body and image hashes are equal. A strict mobile body/image subset is `stale_mobile` and is ignored. New content, non-identical same-date records, or independent edits are conflicts. A conflict retains the Desktop ID, shows two read-only versions with an editable result, and preserves the union of both image sets by default.
