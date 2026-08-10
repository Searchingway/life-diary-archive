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
  due_date: string,
  tasks: PlanMemo["extra"]["tasks"] = [],
): PlanMemo {
  return {
    id,
    module: "plans",
    title: id,
    body: "",
    date: "2026-08-01",
    status,
    type: "add",
    extra: { schema_version: 2, goal: "", start_date: "2026-08-01", due_date, priority: "中", notes: "", tags: [], tasks, plan_type: "add" },
    createdAt: "2026-08-01T00:00:00.000Z",
    updatedAt: "2026-08-01T00:00:00.000Z",
  };
}

describe("plans domain", () => {
  it("creates plans with the light-weight default structure", () => {
    expect(emptyPlan()).toMatchObject({
      module: "plans",
      status: "未开始",
      type: "add",
      extra: { schema_version: 2, goal: "", start_date: expect.any(String), due_date: "", priority: "中", notes: "", tags: [], tasks: [], plan_type: "add" },
    });
  });

  it("calculates progress exclusively from completed tasks", () => {
    expect(planProgress([])).toBe(0);
    expect(planProgress([{ id: "one", title: "任务", scheduled_date: "", done: true, note: "" }, { id: "two", title: "任务", scheduled_date: "", done: false, note: "" }])).toBe(50);
  });

  it("ranks overdue plans before today tasks and inactive plans", () => {
    const result = sortPlans(
      [
        plan("paused", "已暂停", "2026-08-01"),
        plan("done", "已完成", "2026-08-01"),
        plan("not-started", "未开始", "2026-08-20"),
        plan("in-progress", "进行中", "2026-08-20"),
        plan("today", "未开始", "2026-08-20", [{ id: "today-task", title: "今日任务", scheduled_date: "2026-08-07", done: false, note: "" }]),
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
          { id: "today", title: "今天做", scheduled_date: "2026-08-07", done: false, note: "" },
          { id: "done", title: "今天已完成", scheduled_date: "2026-08-07", done: true, note: "" },
          { id: "tomorrow", title: "明天做", scheduled_date: "2026-08-08", done: false, note: "" },
        ]),
      ],
      "2026-08-07",
    );

    expect(tasks).toEqual([{ planId: "plan-1", planTitle: "plan-1", task: { id: "today", title: "今天做", scheduled_date: "2026-08-07", done: false, note: "" } }]);
  });

  it("persists a checked plan task through the repository", async () => {
    const repository = createMemoryRecordRepository();
    const saved = await repository.save({
      ...emptyPlan(),
      title: "持久化计划",
      extra: {
        ...emptyPlan().extra,
        tasks: [{ id: "task-1", title: "可完成任务", scheduled_date: "2026-08-07", done: false, note: "" }],
      },
    });

    await repository.save({
      ...saved,
      extra: { ...saved.extra, notes: saved.body, tasks: [{ id: "task-1", title: "可完成任务", scheduled_date: "2026-08-07", done: true, note: "" }] },
    });

    expect((await repository.list("plans"))[0].extra.tasks).toEqual([
      { id: "task-1", title: "可完成任务", scheduled_date: "2026-08-07", done: true, note: "" },
    ]);
  });

  it("keeps canonical scheduled_date tasks visible in the Today timeline", () => {
    const tasks = selectTodayPlanTasks(
      [
        {
          ...plan("canonical", "进行中", "2026-08-08"),
          extra: { schema_version: 2, goal: "", start_date: "2026-08-01", due_date: "2026-08-08", priority: "中", notes: "", tags: [], plan_type: "add", tasks: [{ id: "today", title: "Canonical task", scheduled_date: "2026-08-07", done: false, note: "" }] },
        } as PlanMemo,
      ],
      "2026-08-07",
    );
    expect(tasks.map((item) => item.task.id)).toEqual(["today"]);
  });

  it("persists legacy plan input as canonical V2 while preserving extensions", async () => {
    const repository = createMemoryRecordRepository();
    const saved = await repository.save({
      module: "plans",
      title: "Canonical",
      body: "Notes",
      date: "2026-08-01",
      status: "搁置",
      type: "reduce",
      extra: { startDate: "2026-08-01", deadline: "2026-08-02", priority: "普通", task_extension: true, tasks: [{ id: "one", title: "Task", date: "2026-08-01", done: false }] },
    });

    expect(saved).toMatchObject({
      status: "已暂停",
      type: "subtract",
      body: "Notes",
      extra: { schema_version: 2, start_date: "2026-08-01", due_date: "2026-08-02", notes: "Notes", priority: "中", task_extension: true, tasks: [{ scheduled_date: "2026-08-01" }] },
    });
    expect(saved.extra).not.toHaveProperty("startDate");
    expect(saved.extra).not.toHaveProperty("deadline");
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
