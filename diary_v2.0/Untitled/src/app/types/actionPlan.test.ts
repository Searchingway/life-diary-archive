import { afterEach, describe, expect, it, vi } from "vitest";
import { createEmptyTask, ganttBarDays, toActionPlanTaskV2 } from "./actionPlan";

afterEach(() => vi.useRealTimers());

describe("action task normalization", () => {
  it("retains canonical and legacy estimates, including zero", () => {
    expect(toActionPlanTaskV2({ id: "a", title: "task", estimatedMinutes: 45 }).estimatedMinutes).toBe(45);
    expect(toActionPlanTaskV2({ id: "b", title: "task", estimated_minutes: 25 }).estimatedMinutes).toBe(25);
    expect(toActionPlanTaskV2({ id: "c", title: "task", estimatedMinutes: 0 }).estimatedMinutes).toBe(0);
  });
  it("renders a completed task at full progress", () => {
    const task = toActionPlanTaskV2({ id: "a", title: "task", done: true, progress: 20, status: "doing" });
    expect(task.progress).toBe(100);
    expect(task.status).toBe("done");
  });
  it("keeps imported progress within the supported range", () => {
    expect(toActionPlanTaskV2({ id: "a", title: "task", progress: 150 }).progress).toBe(100);
    expect(toActionPlanTaskV2({ id: "b", title: "task", progress: -5 }).progress).toBe(0);
  });
  it("creates a task on the local calendar date after midnight", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 9, 15, 0, 30));
    expect(createEmptyTask().scheduledDate).toBe("2026-10-15");
  });
  it("bases gantt width on dates independently of estimates", () => {
    const task = createEmptyTask("2026-10-15");
    task.endDate = "2026-10-17";
    expect(ganttBarDays({ ...task, estimatedMinutes: 1 })).toBe(3);
    expect(ganttBarDays({ ...task, estimatedMinutes: 999 })).toBe(3);
  });
});
