export type ModuleKey =
  | "entries"
  | "footprints"
  | "plans"
  | "action_plans"
  | "thoughts"
  | "resources"
  | "info_memos"
  | "notes"
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

export interface AppSettings {
  export_dir: string;
  updated_at?: string;
}

export interface FootprintVisit {
  id: string;
  date: string;
  thought?: string;
  images?: EntryImage[];
}

export interface ImageUploadFile {
  name: string;
  data: string;
  label?: string;
}

export interface ExportResult {
  docx_path?: string;
  pdf_path?: string;
  count?: number;
  output_dir?: string;
  txt_path?: string;
  md_path?: string;
  zip_path?: string;
  manifest_path?: string;
  module_key?: ModuleKey;
  module_label?: string;
  files?: Array<{ module_key: ModuleKey; module_label: string; txt_path?: string; docx_path?: string; md_path?: string; count: number }>;
}

export interface SyncConflictVersion {
  id: string;
  title?: string;
  body: string;
  updated_at?: string;
  images?: Array<{ file_name: string; label?: string }>;
}

export interface SyncConflict {
  id: string;
  kind: "conflict";
  module: "entries" | "footprints" | "plans" | "info_memos";
  canonical_id: string;
  desktop: SyncConflictVersion;
  mobile: SyncConflictVersion;
  reason: string;
  resolved: boolean;
  desktop_changed_lines?: number[];
  mobile_changed_lines?: number[];
  merge_candidate?: string;
}

export interface SyncSession {
  id: string;
  created_at: string;
  safety_backup: string;
  summary: Record<"new" | "unchanged" | "stale_mobile" | "duplicate" | "conflict", number>;
  conflicts: SyncConflict[];
  committed_at?: string;
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

export function getSettings(): Promise<AppSettings> {
  return request<AppSettings>("/api/settings");
}

export function saveSettings(settings: Partial<AppSettings>): Promise<AppSettings> {
  return request<AppSettings>("/api/settings", {
    method: "POST",
    body: JSON.stringify(settings),
  });
}

export function selectExportDirectory(): Promise<AppSettings> {
  return request<AppSettings>("/api/actions/select-export-dir", { method: "POST" });
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

export function uploadFootprintVisitImages(
  footprintId: string,
  visitId: string,
  files: ImageUploadFile[],
): Promise<RecordItem> {
  return request<RecordItem>(
    `/api/modules/footprints/${encodeURIComponent(footprintId)}/visits/${encodeURIComponent(visitId)}/images`,
    {
      method: "POST",
      body: JSON.stringify({ files }),
    },
  );
}

export function saveFootprintVisit(
  footprintId: string,
  payload: { date: string; thought?: string },
): Promise<RecordItem> {
  return request<RecordItem>(`/api/modules/footprints/${encodeURIComponent(footprintId)}/visits`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateFootprintVisitImages(
  footprintId: string,
  visitId: string,
  images: Array<{ file_name: string; label?: string }>,
): Promise<RecordItem> {
  return request<RecordItem>(
    `/api/modules/footprints/${encodeURIComponent(footprintId)}/visits/${encodeURIComponent(visitId)}/images`,
    {
      method: "PUT",
      body: JSON.stringify({ images }),
    },
  );
}

export function classifyEntryImages(
  entryId: string,
  payload: { footprint_id: string; date: string; images: string[] },
): Promise<{ ok: true; copied: number; footprint?: RecordItem }> {
  return request<{ ok: true; copied: number; footprint?: RecordItem }>(
    `/api/modules/entries/${encodeURIComponent(entryId)}/classify-images`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function promoteLightPlan(planId: string): Promise<RecordItem> {
  return request<RecordItem>(`/api/modules/plans/${encodeURIComponent(planId)}/promote-action`, {
    method: "POST",
  });
}

export function exportAllEntries(): Promise<ExportResult> {
  return request<ExportResult>("/api/modules/entries/export-all", {
    method: "POST",
  });
}

export function exportAllEntriesTxt(): Promise<ExportResult> {
  return request<ExportResult>("/api/modules/entries/export-txt", {
    method: "POST",
  });
}

export function exportModuleTxt(moduleKey: ModuleKey): Promise<ExportResult> {
  return request<ExportResult>(`/api/modules/${moduleKey}/export-txt`, {
    method: "POST",
  });
}

export function exportNotesMarkdown(): Promise<ExportResult> {
  return request<ExportResult>("/api/modules/notes/export-md", {
    method: "POST",
  });
}

export function exportFootprintsWord(): Promise<ExportResult> {
  return request<ExportResult>("/api/modules/footprints/export-word", {
    method: "POST",
  });
}

export function exportAllModules(): Promise<ExportResult> {
  return request<ExportResult>("/api/export/all", {
    method: "POST",
  });
}

export function selectMobileSnapshotZip(): Promise<{ zip_path: string }> {
  return request<{ zip_path: string }>("/api/sync/select-mobile-zip", { method: "POST" });
}

export function importMobileSnapshot(zipPath: string): Promise<SyncSession> {
  return request<SyncSession>("/api/sync/import-mobile", { method: "POST", body: JSON.stringify({ zip_path: zipPath }) });
}

export function getSyncSession(sessionId: string): Promise<SyncSession> {
  return request<SyncSession>(`/api/sync/sessions/${encodeURIComponent(sessionId)}`);
}

export function resolveEntrySyncConflict(sessionId: string, conflictId: string, body: string, title?: string): Promise<SyncConflict> {
  return request<SyncConflict>(`/api/sync/sessions/${encodeURIComponent(sessionId)}/resolve-entry`, { method: "POST", body: JSON.stringify({ conflict_id: conflictId, body, title }) });
}

export function resolveGenericSyncConflict(sessionId: string, conflictId: string, choice: "desktop" | "mobile"): Promise<SyncConflict> {
  return request<SyncConflict>(`/api/sync/sessions/${encodeURIComponent(sessionId)}/resolve-generic`, { method: "POST", body: JSON.stringify({ conflict_id: conflictId, choice }) });
}

export function commitSyncImport(sessionId: string): Promise<{ ok: true; safety_backup: string }> {
  return request<{ ok: true; safety_backup: string }>(`/api/sync/sessions/${encodeURIComponent(sessionId)}/commit`, { method: "POST", body: "{}" });
}

export function exportDesktopCanonicalZip(): Promise<{ zip_path: string }> {
  return request<{ zip_path: string }>("/api/sync/export-canonical", { method: "POST", body: "{}" });
}
