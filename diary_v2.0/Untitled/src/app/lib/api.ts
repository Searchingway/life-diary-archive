export type ModuleKey =
  | "entries"
  | "footprints"
  | "plans"
  | "action_plans"
  | "thoughts"
  | "resources"
  | "info_memos"
  | "observations"
  | "lessons"
  | "self_analysis"
  | "works";

export interface ModuleInfo {
  key: ModuleKey;
  label: string;
  count: number;
  latest: string;
}

export interface RecordItem {
  id: string;
  title: string;
  subtitle: string;
  body: string;
  date: string;
  updated_at: string;
  status?: string;
  type?: string;
  extra?: Record<string, unknown>;
}

export interface Overview {
  data_root: string;
  legacy_data_root: string;
  migrated_from_legacy: boolean;
  dashboard_stats: DashboardStats;
  modules: ModuleInfo[];
  recent: Array<RecordItem & { module: string; module_key: ModuleKey }>;
}

export interface DashboardStats {
  month_diary_count: number;
  month_diary_words: number;
  month_diary_images: number;
  month_completed_plans: number;
  year_diary_count: number;
  year_diary_words: number;
  year_diary_images: number;
  year_completed_plans: number;
  action_plan_count: number;
  active_action_plan_count: number;
  today_pending_tasks: number;
}

export interface EntryImage {
  file_name: string;
  label?: string;
  url: string;
}

export interface ImageUploadFile {
  name: string;
  data: string;
  label?: string;
}

export interface ExportResult {
  docx_path: string;
  pdf_path: string;
  count?: number;
  output_dir?: string;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText);
  }
  return response.json();
}

export function getOverview(): Promise<Overview> {
  return request<Overview>("/api/overview");
}

export function listRecords(moduleKey: ModuleKey, query = ""): Promise<RecordItem[]> {
  return request<RecordItem[]>(`/api/modules/${moduleKey}?q=${encodeURIComponent(query)}`);
}

export function saveRecord(moduleKey: ModuleKey, record: RecordItem): Promise<RecordItem> {
  return request<RecordItem>(`/api/modules/${moduleKey}`, {
    method: "POST",
    body: JSON.stringify(record),
  });
}

export function deleteRecord(moduleKey: ModuleKey, id: string): Promise<{ ok: true }> {
  return request<{ ok: true }>(`/api/modules/${moduleKey}/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export function openDataRoot(): Promise<{ ok: true }> {
  return request<{ ok: true }>("/api/actions/open-data-root", { method: "POST" });
}

export function uploadEntryImages(entryId: string, files: ImageUploadFile[]): Promise<RecordItem> {
  return request<RecordItem>(`/api/modules/entries/${encodeURIComponent(entryId)}/images`, {
    method: "POST",
    body: JSON.stringify({ files }),
  });
}

export function updateEntryImages(
  entryId: string,
  images: Array<{ file_name: string; label?: string }>,
): Promise<RecordItem> {
  return request<RecordItem>(`/api/modules/entries/${encodeURIComponent(entryId)}/images`, {
    method: "PUT",
    body: JSON.stringify({ images }),
  });
}

export function exportAllEntries(): Promise<ExportResult> {
  return request<ExportResult>("/api/modules/entries/export-all", {
    method: "POST",
  });
}
