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
  modules: ModuleInfo[];
  recent: Array<RecordItem & { module: string; module_key: ModuleKey }>;
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
