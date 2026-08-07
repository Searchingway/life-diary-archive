import type { ArchiveRecord, NewRecord } from "./models";
import { today } from "./models";

export const PLAN_STATUSES = ["未开始", "进行中", "已完成", "已暂停"] as const;
export type PlanStatus = (typeof PLAN_STATUSES)[number];

export const PLAN_PRIORITIES = ["高", "中", "低"] as const;
export type PlanPriority = (typeof PLAN_PRIORITIES)[number];

export interface PlanTask {
  id: string;
  title: string;
  date?: string;
  done: boolean;
  note?: string;
}

export interface PlanExtra extends Record<string, unknown> {
  goal: string;
  startDate: string;
  deadline: string;
  priority: PlanPriority;
  tasks: PlanTask[];
}

export interface PlanMemo extends Omit<ArchiveRecord, "module" | "status" | "extra"> {
  module: "plans";
  status: PlanStatus;
  extra: PlanExtra;
}

export interface TodayPlanTask {
  planId: string;
  planTitle: string;
  task: PlanTask;
}

export function emptyPlan(): NewRecord {
  return {
    module: "plans",
    title: "",
    body: "",
    date: today(),
    status: "未开始",
    type: "计划",
    extra: { goal: "", startDate: today(), deadline: "", priority: "中", tasks: [] },
  };
}

export function planProgress(tasks: PlanTask[]): number {
  if (!tasks.length) return 0;
  return Math.round((tasks.filter((task) => task.done).length / tasks.length) * 100);
}

function deadlineSortValue(plan: PlanMemo): string {
  return plan.extra.deadline || "9999-12-31";
}

function isOverdue(plan: PlanMemo, selectedDate: string): boolean {
  return Boolean(plan.extra.deadline && plan.extra.deadline < selectedDate && plan.status !== "已完成" && plan.status !== "已暂停");
}

function hasOpenTaskOn(plan: PlanMemo, selectedDate: string): boolean {
  return plan.extra.tasks.some((task) => task.date === selectedDate && !task.done);
}

export function sortPlans(plans: PlanMemo[], selectedDate = today()): PlanMemo[] {
  const rank = (plan: PlanMemo): number => {
    if (isOverdue(plan, selectedDate)) return 0;
    if (hasOpenTaskOn(plan, selectedDate)) return 1;
    if (plan.status === "进行中") return 2;
    if (plan.status === "未开始") return 3;
    if (plan.status === "已完成") return 4;
    return 5;
  };

  return [...plans].sort((left, right) => {
    const rankDifference = rank(left) - rank(right);
    if (rankDifference) return rankDifference;
    return deadlineSortValue(left).localeCompare(deadlineSortValue(right)) || left.title.localeCompare(right.title);
  });
}

export function selectTodayPlanTasks(plans: PlanMemo[], selectedDate = today()): TodayPlanTask[] {
  return plans.flatMap((plan) =>
    plan.extra.tasks
      .filter((task) => task.date === selectedDate && !task.done)
      .map((task) => ({ planId: plan.id, planTitle: plan.title, task })),
  );
}
