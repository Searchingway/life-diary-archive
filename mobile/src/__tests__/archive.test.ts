import { describe, expect, it } from "vitest";

import { deserializeArchiveRecords, serializeArchiveRecords } from "../compat/archive";
import type { ArchiveRecord } from "../domain/models";

describe("archive compatibility", () => {
  it("restores an old orders-only archive without requiring plans", () => {
    const records: ArchiveRecord[] = [
      {
        id: "legacy-order-1",
        module: "orders",
        title: "历史接单",
        body: "旧备份备注",
        date: "2026-06-20",
        status: "已接单",
        type: "接单记录",
        extra: { customer: "客户" },
        createdAt: "2026-06-20T10:00:00.000Z",
        updatedAt: "2026-06-20T10:00:00.000Z",
      },
    ];

    const files = serializeArchiveRecords(records);
    expect(Object.keys(files).some((path) => path.startsWith("Diary/plans/"))).toBe(false);
    expect(deserializeArchiveRecords(files)).toEqual([{ ...records[0], deleted: false }]);
  });

  it("round-trips diary, footprint, and order records without losing content", () => {
    const records: ArchiveRecord[] = [
      {
        id: "entry-1",
        module: "diary",
        title: "六月二十三日",
        body: "正文",
        date: "2026-06-23",
        status: "",
        type: "",
        extra: { images: [{ fileName: "one.jpg", label: "校门", uri: "" }] },
        createdAt: "2026-06-23T10:00:00.000Z",
        updatedAt: "2026-06-23T10:00:00.000Z",
      },
      {
        id: "place-1",
        module: "footprints",
        title: "东北农业大学",
        body: "地点描述",
        date: "2026-06-12",
        status: "",
        type: "",
        extra: {
          visits: [
            {
              id: "visit-1",
              date: "2026-06-12",
              thought: "访问记录",
              images: [],
              createdAt: "2026-06-12T10:00:00.000Z",
              updatedAt: "2026-06-12T10:00:00.000Z",
            },
          ],
        },
        createdAt: "2026-06-12T10:00:00.000Z",
        updatedAt: "2026-06-12T10:00:00.000Z",
      },
      {
        id: "order-1",
        module: "orders",
        title: "小程序",
        body: "备注",
        date: "2026-06-20",
        status: "已接单",
        type: "接单记录",
        extra: { customer: "客户甲", price: 3000 },
        createdAt: "2026-06-20T10:00:00.000Z",
        updatedAt: "2026-06-20T10:00:00.000Z",
      },
      {
        id: "plan-1",
        module: "plans",
        title: "完成第一阶段",
        body: "计划备注",
        date: "2026-06-21",
        status: "进行中",
        type: "计划",
        extra: {
          goal: "交付版本",
          startDate: "2026-06-21",
          deadline: "2026-06-30",
          priority: "高",
          tasks: [{ id: "task-1", title: "补齐测试", date: "2026-06-23", done: false }],
        },
        createdAt: "2026-06-21T10:00:00.000Z",
        updatedAt: "2026-06-21T10:00:00.000Z",
      },
    ];

    const files = serializeArchiveRecords(records);
    const restored = deserializeArchiveRecords(files);

    expect(restored).toEqual(records.map((record) => ({ ...record, deleted: false })));
    expect(files["Diary/entries/entry-1/content.md"]).toBe("正文");
    expect(files["Diary/footprints/place-1/footprint.json"]).toContain("东北农业大学");
    expect(files["Diary/info_memos/order-1/info_memo.json"]).toContain("已接单");
    expect(files["Diary/plans/plan-1/plan.json"]).toContain("完成第一阶段");
  });
});
