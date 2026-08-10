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

Plans use `schema_version: 2`; the canonical shared fixture is `shared/sync/fixtures/plan_v2_full.json`. Readers migrate V1 aliases losslessly: `deadline` to `due_date`, `startDate` to `start_date`, plan `note` to `notes`, and task `scheduledDate` / `date` to `scheduled_date`. Those known aliases are removed from canonical V2 output; unknown extension fields remain unchanged and migration is idempotent.

The only canonical plan statuses are `未开始`, `进行中`, `已暂停`, and `已完成`. Both `搁置` and `暂停` normalise to `已暂停`; priority `普通` normalises to `中`; and historical `plan_type: reduce` normalises to `subtract`. Desktop edits and canonical ZIP output always write those canonical values, while retaining tags and subtract-plan extension fields.

## Entry conflict policy

`updated_at` is display-only. Same-ID entries are `unchanged` only when normalised date/title/body and image hashes are equal. A strict mobile body/image subset is `stale_mobile` and is ignored. New content, non-identical same-date records, or independent edits are conflicts. A conflict retains the Desktop ID, shows PC title/body, editable final title/body, and Mobile title/body. Its initial body candidate preserves shared lines once and every unique line from both copies using conflict markers where necessary. Image union preserves `file_name` and `label`; for a matching hash, a non-empty Desktop label wins, otherwise Mobile's non-empty label is used.

## Footprints, backup, and commit safety

Footprint comparison fingerprints semantic file contents rather than mtimes: `footprint.json`, `summary.md`, every `visits/*/visit.json`, `visits/*/thought.md`, visit images, and place images. Any content difference is staged as a conflict.

Before preflight stages a snapshot, Desktop creates a standard LifeDiary backup ZIP through the shared backup service, including its official `manifest.json`; it can be validated and restored by the normal backup flow. A successful commit uses one global mutation lock around its directory swap and all HTTP write endpoints, then removes the extracted snapshot and temporary pre-commit/working trees while retaining the safety ZIP and a small session metadata file.
