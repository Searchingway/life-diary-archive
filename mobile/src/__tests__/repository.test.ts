import { describe, expect, it } from "vitest";

import { createMemoryRecordRepository } from "../db/repository";

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
});
