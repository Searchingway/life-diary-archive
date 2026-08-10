import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  createMobileSnapshotManifest,
  migratePlanToV2,
  parseDesktopCanonicalTextFiles,
  validateArchivePaths,
} from "../compat/syncProtocol";
import { consumeIncomingUri, normalizeIncomingSystemPath } from "../compat/incomingIntent";

describe("Sync Protocol V1 mobile compatibility", () => {
  it("migrates legacy plans to canonical V2 without retaining aliases", () => {
    const migrated = migratePlanToV2({
      id: "plan-1",
      title: "Read",
      startDate: "2026-08-01",
      deadline: "2026-08-31",
      note: "Keep notes",
      status: "搁置",
      priority: "普通",
      plan_type: "reduce",
      unknown_extension: { keep: true },
      tasks: [{ id: "task-1", title: "Chapter", scheduledDate: "2026-08-02", date: "old", done: false, note: "task note" }],
    });

    expect(migrated).toMatchObject({
      schema_version: 2,
      id: "plan-1",
      start_date: "2026-08-01",
      due_date: "2026-08-31",
      notes: "Keep notes",
      status: "已暂停",
      priority: "中",
      plan_type: "subtract",
      unknown_extension: { keep: true },
      tasks: [{ id: "task-1", scheduled_date: "2026-08-02", note: "task note" }],
    });
    expect(migrated).not.toHaveProperty("startDate");
    expect(migrated).not.toHaveProperty("deadline");
    expect(migrated).not.toHaveProperty("note");
    expect(migrated.tasks[0]).not.toHaveProperty("scheduledDate");
    expect(migrated.tasks[0]).not.toHaveProperty("date");
    expect(migratePlanToV2(migrated)).toEqual(migrated);
  });

  it("round-trips the shared Plan V2 fixture semantically", () => {
    const fixture = JSON.parse(readFileSync(resolve(__dirname, "../../../shared/sync/fixtures/plan_v2_full.json"), "utf8"));
    expect(migratePlanToV2(fixture)).toEqual(fixture);
  });

  it("creates the exact mobile snapshot manifest", () => {
    expect(createMobileSnapshotManifest("2026-08-10T00:00:00.000Z")).toEqual({
      app: "LifeDiary",
      protocol_version: 1,
      package_role: "mobile_snapshot",
      source_platform: "mobile",
      created_at: "2026-08-10T00:00:00.000Z",
      schema_versions: { plans: 2 },
    });
  });

  it("accepts desktop canonical files while rejecting mobile snapshots and unsafe paths", () => {
    const files = {
      "manifest.json": JSON.stringify({
        app: "LifeDiary",
        protocol_version: 1,
        package_role: "desktop_canonical",
        source_platform: "desktop",
        created_at: "2026-08-10T00:00:00.000Z",
        schema_versions: { plans: 2 },
      }),
      "Diary/entries/pc123/entry.json": JSON.stringify({ id: "pc123", date: "2026-08-10", title: "PC", images: [{ file_name: "cover.jpg", label: "Desktop cover" }] }),
      "Diary/entries/pc123/content.md": "Desktop body",
    };
    expect(parseDesktopCanonicalTextFiles(files).records[0]).toMatchObject({
      id: "pc123",
      module: "diary",
      title: "PC",
      body: "Desktop body",
      extra: { images: [{ fileName: "cover.jpg", label: "Desktop cover", uri: "" }] },
    });
    expect(() => parseDesktopCanonicalTextFiles({ ...files, "manifest.json": JSON.stringify({ package_role: "mobile_snapshot" }) })).toThrow(/desktop canonical/i);
    expect(() => validateArchivePaths(["manifest.json", "Diary/entries/pc123/entry.json", "../escape.json"])).toThrow(/unsafe/i);
    expect(() => validateArchivePaths(["manifest.json", "manifest.json"])).toThrow(/duplicate/i);
  });

  it("routes one supported Android ZIP URI to Data and suppresses a duplicate intent", () => {
    const uri = "content://com.tencent.mm.external.fileprovider/cache/LifeDiary-Desktop-Canonical.zip";
    expect(normalizeIncomingSystemPath(uri)).toBe(`/data?incoming=${encodeURIComponent(uri)}`);
    expect(consumeIncomingUri(uri, 1000)).toBe(true);
    expect(consumeIncomingUri(uri, 1100)).toBe(false);
    expect(consumeIncomingUri(uri, 20_000)).toBe(true);
    expect(normalizeIncomingSystemPath("content://provider/not-a-zip.txt")).toBe("/data");
  });
});
