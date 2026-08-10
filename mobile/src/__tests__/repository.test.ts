import { describe, expect, it } from "vitest";

import { createMemoryRecordRepository } from "../db/repository";
import type { ModuleKey } from "../domain/models";

describe("record repository contract", () => {
  it("saves, searches, and soft deletes records", async () => {
    const repository = createMemoryRecordRepository();
    const saved = await repository.save({
      module: "diary",
      title: "晨跑",
      body: "今天沿着江边跑步。",
      date: "2026-06-23",
      status: "",
      type: "",
      extra: {},
    });

    expect((await repository.list("diary", "江边")).map((item) => item.id)).toEqual([saved.id]);

    await repository.softDelete(saved.id);

    expect(await repository.list("diary")).toEqual([]);
    expect(await repository.get(saved.id, true)).toMatchObject({ id: saved.id, deleted: true });
  });

  it("replaces only shared modules during Desktop Canonical import", async () => {
    const repository = createMemoryRecordRepository();
    const existingDiary = await repository.save({ module: "diary", title: "old", body: "", date: "2026-08-01", status: "", type: "", extra: {} });
    const localOnly = await repository.save({ module: "local_only" as ModuleKey, title: "local", body: "", date: "2026-08-01", status: "", type: "", extra: {} });

    await repository.replaceSharedModules([
      { ...existingDiary, id: "pc-id", title: "desktop", createdAt: "2026-08-10T00:00:00.000Z", updatedAt: "2026-08-10T00:00:00.000Z", deleted: false },
    ]);

    expect(await repository.get(existingDiary.id, true)).toBeNull();
    expect((await repository.list("diary")).map((record) => record.id)).toEqual(["pc-id"]);
    expect(await repository.get(localOnly.id)).toMatchObject({ title: "local" });
  });
});
