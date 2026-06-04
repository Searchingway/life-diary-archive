/** V2 task model supporting Today / Gantt / Chain three views. */
export interface ActionPlanTaskV2 {
  id: string;
  title: string;

  /** Today View — single-date grouping, may be empty */
  scheduledDate?: string;
  /** Gantt View — bar left edge */
  startDate: string;
  /** Gantt View — bar right edge; width = endDate - startDate + 1 day */
  endDate: string;
  /** Gantt View — 0-100 fill inside the bar */
  progress: number;

  /** Chain View — predecessor task ids */
  dependsOn: string[];
  /** Chain View — node position */
  chainX?: number | null;
  chainY?: number | null;

  /** Display only — never used for Gantt bar width */
  estimatedMinutes: number;
  done: boolean;
  status: "todo" | "doing" | "done" | "blocked";
  note: string;
}

export type ActionPlanView = "today" | "gantt" | "chain";

/** Legacy task from server — may have only `date` + `done`. */
export interface LegacyTask {
  id: string;
  title: string;
  date?: string;
  time?: string;
  estimated_minutes?: number;
  done?: boolean;
  note?: string;
  startDate?: string;
  endDate?: string;
  progress?: number;
  dependsOn?: string[];
  chainX?: number | null;
  chainY?: number | null;
  status?: string;
  scheduledDate?: string;
}

/** Normalize old task data to V2 fields. */
export function toActionPlanTaskV2(raw: LegacyTask): ActionPlanTaskV2 {
  const date = raw.date || raw.scheduledDate || raw.startDate || "";
  const startDate = raw.startDate || date || "";
  const endDate = raw.endDate || date || "";
  const done = !!raw.done;
  return {
    id: raw.id,
    title: raw.title || "未命名子任务",
    scheduledDate: raw.scheduledDate || date || undefined,
    startDate,
    endDate: endDate,
    progress: raw.progress ?? (done ? 100 : 0),
    dependsOn: Array.isArray(raw.dependsOn) ? raw.dependsOn : [],
    chainX: raw.chainX ?? null,
    chainY: raw.chainY ?? null,
    estimatedMinutes: raw.estimated_minutes || raw.estimatedMinutes === 0 ? raw.estimated_minutes : 0,
    done,
    status: (raw.status as ActionPlanTaskV2["status"]) || (done ? "done" : "todo"),
    note: raw.note || "",
  };
}

export function createEmptyTask(date = new Date().toISOString().slice(0, 10)): ActionPlanTaskV2 {
  return {
    id: crypto.randomUUID(),
    title: "新子任务",
    scheduledDate: date,
    startDate: date,
    endDate: date,
    progress: 0,
    dependsOn: [],
    chainX: null,
    chainY: null,
    estimatedMinutes: 30,
    done: false,
    status: "todo",
    note: "",
  };
}

/** Group tasks by date key. Uses scheduledDate → startDate fallback. */
export function groupTasksByDate(tasks: ActionPlanTaskV2[]): Record<string, ActionPlanTaskV2[]> {
  const groups: Record<string, ActionPlanTaskV2[]> = {};
  for (const t of tasks) {
    const key = t.scheduledDate || t.startDate || "未安排";
    (groups[key] ??= []).push(t);
  }
  return groups;
}

/** Sort date keys ascending. */
export function sortDateKeys(groups: Record<string, ActionPlanTaskV2[]>): string[] {
  return Object.keys(groups).sort((a, b) => {
    if (a === "未安排") return 1;
    if (b === "未安排") return -1;
    return a.localeCompare(b);
  });
}

/** Gantt bar width in days. */
export function ganttBarDays(task: ActionPlanTaskV2): number {
  if (!task.startDate || !task.endDate) return 1;
  const start = new Date(task.startDate);
  const end = new Date(task.endDate);
  return Math.max(1, (end.getTime() - start.getTime()) / 86400000 + 1);
}
