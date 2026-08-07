import { describe, expect, it } from "vitest";

import { createMemoryRecordRepository } from "../db/repository";
import {
  emptyPlan,
  planProgress,
  selectTodayPlanTasks,
  sortPlans,
  type PlanMemo,
} from "../domain/plans";
import { recordsForDate } from "../domain/today";

function plan(
  id: string,
  status: PlanMemo["status"],
  deadline: string,
  tasks: PlanMemo["extra"]["tasks"] = [],
): PlanMemo {
  return {
    id,
    module: "plans",
    title: id,
    body: "",
    date: "2026-08-01",
    status,
    type: "计划",
    extra: { goal: "", startDate: "2026-08-01", deadline, priority: "中", tasks },
    createdAt: "2026-08-01T00:00:00.000Z",
    updatedAt: "2026-08-01T00:00:00.000Z",
  };
}

describe("plans domain", () => {
  it("creates plans with the light-weight default structure", () => {
    expect(emptyPlan()).toMatchObject({
      module: "plans",
      status: "未开始",
      type: "计划",
      extra: { goal: "", startDate: expect.any(String), deadline: "", priority: "中", tasks: [] },
    });
  });

  it("calculates progress exclusively from completed tasks", () => {
    expect(planProgress([])).toBe(0);
    expect(planProgress([{ id: "one", title: "任务", done: true }, { id: "two", title: "任务", done: false }])).toBe(50);
  });

  it("ranks overdue plans before today tasks and inactive plans", () => {
    const result = sortPlans(
      [
        plan("paused", "已暂停", "2026-08-01"),
        plan("done", "已完成", "2026-08-01"),
        plan("not-started", "未开始", "2026-08-20"),
        plan("in-progress", "进行中", "2026-08-20"),
        plan("today", "未开始", "2026-08-20", [{ id: "today-task", title: "今日任务", date: "2026-08-07", done: false }]),
        plan("overdue", "进行中", "2026-08-06"),
      ],
      "2026-08-07",
    );

    expect(result.map((record) => record.id)).toEqual(["overdue", "today", "in-progress", "not-started", "done", "paused"]);
  });

  it("selects only unfinished tasks scheduled for the chosen day", () => {
    const tasks = selectTodayPlanTasks(
      [
        plan("plan-1", "进行中", "", [
          { id: "today", title: "今天做", date: "2026-08-07", done: false },
          { id: "done", title: "今天已完成", date: "2026-08-07", done: true },
          { id: "tomorrow", title: "明天做", date: "2026-08-08", done: false },
        ]),
      ],
      "2026-08-07",
    );

    expect(tasks).toEqual([{ planId: "plan-1", planTitle: "plan-1", task: { id: "today", title: "今天做", date: "2026-08-07", done: false } }]);
  });

  it("persists a checked plan task through the repository", async () => {
    const repository = createMemoryRecordRepository();
    const saved = await repository.save({
      ...emptyPlan(),
      title: "持久化计划",
      extra: {
        ...emptyPlan().extra,
        tasks: [{ id: "task-1", title: "可完成任务", date: "2026-08-07", done: false }],
      },
    });

    await repository.save({
      ...saved,
      extra: { ...saved.extra, tasks: [{ id: "task-1", title: "可完成任务", date: "2026-08-07", done: true }] },
    });

    expect((await repository.list("plans"))[0].extra.tasks).toEqual([
      { id: "task-1", title: "可完成任务", date: "2026-08-07", done: true },
    ]);
  });

  it("groups only diary and footprint records relevant to the selected date", () => {
    const result = recordsForDate(
      [
        { ...plan("not-a-timeline-item", "进行中", ""), module: "plans" as const },
        {
          id: "diary-today",
          module: "diary" as const,
          title: "今日随笔",
          body: "",
          date: "2026-08-07",
          status: "",
          type: "",
          extra: {},
          createdAt: "2026-08-07T00:00:00.000Z",
          updatedAt: "2026-08-07T00:00:00.000Z",
        },
        {
          id: "place-with-today-visit",
          module: "footprints" as const,
          title: "图书馆",
          body: "",
          date: "2026-08-01",
          status: "",
          type: "",
          extra: { visits: [{ id: "visit-1", date: "2026-08-07", thought: "自习", images: [], createdAt: "", updatedAt: "" }] },
          createdAt: "2026-08-01T00:00:00.000Z",
          updatedAt: "2026-08-01T00:00:00.000Z",
        },
        {
          id: "diary-tomorrow",
          module: "diary" as const,
          title: "明日随笔",
          body: "",
          date: "2026-08-08",
          status: "",
          type: "",
          extra: {},
          createdAt: "2026-08-08T00:00:00.000Z",
          updatedAt: "2026-08-08T00:00:00.000Z",
        },
      ],
      "2026-08-07",
    );

    expect(result.diaries.map((record) => record.id)).toEqual(["diary-today"]);
    expect(result.footprints.map((record) => record.id)).toEqual(["place-with-today-visit"]);
  });
});
