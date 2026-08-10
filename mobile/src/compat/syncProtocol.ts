import type { ArchiveRecord, FootprintVisit, ImageRef } from "../domain/models";

export const PROTOCOL_VERSION = 1;
export const SHARED_MODULES = ["diary", "footprints", "plans", "orders"] as const;

type JsonObject = Record<string, unknown>;
export type ProtocolManifest = {
  app: "LifeDiary";
  protocol_version: 1;
  package_role: "mobile_snapshot" | "desktop_canonical";
  source_platform: "mobile" | "desktop";
  created_at: string;
  schema_versions: { plans: 2 };
};

export type CanonicalPlan = JsonObject & {
  schema_version: 2;
  id: string;
  title: string;
  goal: string;
  start_date: string;
  due_date: string;
  status: "未开始" | "进行中" | "已暂停" | "已完成";
  priority: "高" | "中" | "低";
  notes: string;
  tags: string[];
  tasks: Array<JsonObject & { id: string; title: string; scheduled_date: string; done: boolean; note: string }>;
  plan_type: "add" | "subtract";
};

const statuses = new Set(["未开始", "进行中", "已暂停", "已完成"]);
const priorities = new Set(["高", "中", "低"]);

function object(value: unknown): JsonObject {
  return value && typeof value === "object" && !Array.isArray(value) ? { ...(value as JsonObject) } : {};
}

function text(value: unknown): string {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

function json(value: string | undefined): JsonObject {
  if (!value) return {};
  try {
    return object(JSON.parse(value));
  } catch {
    throw new Error("Malformed JSON in sync archive");
  }
}

export function validateRecordId(value: string): string {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(value)) throw new Error("Unsafe record ID in sync archive");
  return value;
}

export function migratePlanToV2(value: unknown): CanonicalPlan {
  const source = object(value);
  const planId = text(source.id || source.plan_id);
  const rawStatus = text(source.status || "未开始");
  const status = (rawStatus === "搁置" || rawStatus === "暂停" ? "已暂停" : rawStatus) as CanonicalPlan["status"];
  const rawPriority = text(source.priority || "中");
  const priority = (rawPriority === "普通" ? "中" : rawPriority) as CanonicalPlan["priority"];
  const rawTasks = Array.isArray(source.tasks) ? source.tasks : [];
  const tasks: CanonicalPlan["tasks"] = rawTasks.map((item, index) => {
    const task = object(item);
    const migrated: JsonObject = {
      ...task,
      id: text(task.id || `${planId || "plan"}-task-${index + 1}`),
      title: text(task.title),
      scheduled_date: text(task.scheduled_date || task.scheduledDate || task.date),
      done: Boolean(task.done),
      note: text(task.note),
    };
    delete migrated.scheduledDate;
    delete migrated.date;
    return migrated as CanonicalPlan["tasks"][number];
  });
  const tags = Array.isArray(source.tags) ? source.tags.map(text).filter(Boolean) : [];
  const migrated = {
    ...source,
    schema_version: 2 as const,
    id: planId,
    title: text(source.title),
    goal: text(source.goal),
    start_date: text(source.start_date || source.startDate || source.date),
    due_date: text(source.due_date || source.deadline),
    status: statuses.has(status) ? status : "未开始",
    priority: priorities.has(priority) ? priority : "中",
    notes: text(source.notes || source.note),
    tags,
    tasks,
    plan_type: source.plan_type === "subtract" || source.plan_type === "reduce" ? "subtract" : "add",
    subtract_mode: text(source.subtract_mode),
    trigger_scene: text(source.trigger_scene),
    avoid_behavior: text(source.avoid_behavior),
    reason: text(source.reason),
    alternative_action: text(source.alternative_action),
    created_at: text(source.created_at),
    updated_at: text(source.updated_at),
    deleted: Boolean(source.deleted),
    deleted_at: text(source.deleted_at),
  } as CanonicalPlan;
  delete migrated.startDate;
  delete migrated.deadline;
  delete migrated.note;
  return migrated;
}

export function createMobileSnapshotManifest(createdAt = new Date().toISOString()): ProtocolManifest {
  return {
    app: "LifeDiary",
    protocol_version: 1,
    package_role: "mobile_snapshot",
    source_platform: "mobile",
    created_at: createdAt,
    schema_versions: { plans: 2 },
  };
}

export function validateArchivePaths(paths: string[]): void {
  const seen = new Set<string>();
  for (const path of paths) {
    if (!path || path.startsWith("/") || path.includes("\\") || path.split("/").some((part) => !part || part === "." || part === "..") || seen.has(path)) {
      throw new Error("Unsafe or duplicate sync archive path");
    }
    seen.add(path);
  }
}

function imageRefs(values: unknown): ImageRef[] {
  if (!Array.isArray(values)) return [];
  return values.flatMap((value) => {
    const item = object(value);
    const fileName = text(item.file_name || item.fileName);
    return fileName ? [{ fileName, label: text(item.label), uri: "" }] : [];
  });
}

export function parseDesktopCanonicalTextFiles(files: Record<string, string>): { manifest: ProtocolManifest; records: ArchiveRecord[] } {
  validateArchivePaths(Object.keys(files));
  const manifest = json(files["manifest.json"]) as Partial<ProtocolManifest>;
  if (manifest.app !== "LifeDiary" || manifest.protocol_version !== PROTOCOL_VERSION || manifest.package_role !== "desktop_canonical" || manifest.source_platform !== "desktop") {
    throw new Error("Archive is not a Desktop Canonical package");
  }
  const records: ArchiveRecord[] = [];
  const now = new Date().toISOString();
  for (const path of Object.keys(files)) {
    let match = path.match(/^Diary\/entries\/([^/]+)\/entry\.json$/);
    if (match) {
      const id = validateRecordId(match[1]);
      const data = json(files[path]);
      records.push({ id, module: "diary", title: text(data.title), body: files[`Diary/entries/${id}/content.md`] || "", date: text(data.date), status: "", type: "", extra: { images: imageRefs(data.images) }, createdAt: text(data.created_at) || now, updatedAt: text(data.updated_at) || now, deleted: Boolean(data.deleted) });
      continue;
    }
    match = path.match(/^Diary\/footprints\/([^/]+)\/footprint\.json$/);
    if (match) {
      const id = validateRecordId(match[1]);
      const data = json(files[path]);
      const visits: FootprintVisit[] = Object.keys(files).flatMap((visitPath) => {
        const visitMatch = visitPath.match(new RegExp(`^Diary/footprints/${id}/visits/([^/]+)/visit\\.json$`));
        if (!visitMatch) return [];
        const visitId = validateRecordId(visitMatch[1]);
        const visit = json(files[visitPath]);
        return [{ id: visitId, date: text(visit.date), thought: files[`Diary/footprints/${id}/visits/${visitId}/thought.md`] || "", images: imageRefs(visit.images), createdAt: text(visit.created_at) || now, updatedAt: text(visit.updated_at) || now }];
      });
      records.push({ id, module: "footprints", title: text(data.place_name || data.title), body: files[`Diary/footprints/${id}/summary.md`] || "", date: text(data.date) || visits[0]?.date || "", status: "", type: "", extra: { images: imageRefs(data.images), visits }, createdAt: text(data.created_at) || now, updatedAt: text(data.updated_at) || now, deleted: Boolean(data.deleted) });
      continue;
    }
    match = path.match(/^Diary\/plans\/([^/]+)\/plan\.json$/);
    if (match) {
      const id = validateRecordId(match[1]);
      const plan = migratePlanToV2({ ...json(files[path]), id });
      records.push({ id, module: "plans", title: plan.title, body: plan.notes, date: plan.start_date, status: plan.status, type: plan.plan_type, extra: plan, createdAt: text(plan.created_at) || now, updatedAt: text(plan.updated_at) || now, deleted: Boolean(plan.deleted), deletedAt: text(plan.deleted_at) || undefined });
      continue;
    }
    match = path.match(/^Diary\/info_memos\/([^/]+)\/info_memo\.json$/);
    if (match) {
      const id = validateRecordId(match[1]);
      const data = json(files[path]);
      const extra = object(data.type_fields);
      records.push({ id, module: "orders", title: text(data.title), body: text(data.note || data.main_content), date: text(data.date || extra.order_date), status: text(data.status), type: text(data.info_type), extra, createdAt: text(data.created_at) || now, updatedAt: text(data.updated_at) || now, deleted: Boolean(data.deleted) });
    }
  }
  return { manifest: manifest as ProtocolManifest, records };
}
