import type { ArchiveRecord, FootprintVisit, ImageRef, ModuleKey } from "../domain/models";

export type ArchiveTextFiles = Record<string, string>;

type JsonObject = Record<string, unknown>;

function parseJson(value: string | undefined): JsonObject {
  if (!value) return {};
  const parsed = JSON.parse(value);
  return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
}

function imagesFromExtra(extra: Record<string, unknown>): ImageRef[] {
  return Array.isArray(extra.images) ? (extra.images as ImageRef[]) : [];
}

export function serializeArchiveRecords(records: ArchiveRecord[]): ArchiveTextFiles {
  const files: ArchiveTextFiles = {};
  for (const record of records) {
    if (record.module === "diary") {
      files[`Diary/entries/${record.id}/entry.json`] = JSON.stringify(
        {
          entry_id: record.id,
          title: record.title,
          date: record.date,
          images: imagesFromExtra(record.extra).map((image) => ({
            file_name: image.fileName,
            label: image.label,
            uri: image.uri,
          })),
          created_at: record.createdAt,
          updated_at: record.updatedAt,
          deleted: Boolean(record.deleted),
          content_file: "content.md",
        },
        null,
        2,
      );
      files[`Diary/entries/${record.id}/content.md`] = record.body;
      continue;
    }

    if (record.module === "footprints") {
      const visits = Array.isArray(record.extra.visits) ? (record.extra.visits as FootprintVisit[]) : [];
      files[`Diary/footprints/${record.id}/footprint.json`] = JSON.stringify(
        {
          footprint_id: record.id,
          place_name: record.title,
          date: record.date,
          created_at: record.createdAt,
          updated_at: record.updatedAt,
          deleted: Boolean(record.deleted),
        },
        null,
        2,
      );
      files[`Diary/footprints/${record.id}/summary.md`] = record.body;
      for (const visit of visits) {
        files[`Diary/footprints/${record.id}/visits/${visit.id}/visit.json`] = JSON.stringify(
          {
            visit_id: visit.id,
            date: visit.date,
            images: visit.images.map((image) => ({
              file_name: image.fileName,
              label: image.label,
              uri: image.uri,
            })),
            created_at: visit.createdAt,
            updated_at: visit.updatedAt,
          },
          null,
          2,
        );
        files[`Diary/footprints/${record.id}/visits/${visit.id}/thought.md`] = visit.thought;
      }
      continue;
    }

    files[`Diary/info_memos/${record.id}/info_memo.json`] = JSON.stringify(
      {
        info_memo_id: record.id,
        title: record.title,
        date: record.date,
        status: record.status,
        info_type: record.type || "接单记录",
        type_fields: record.extra,
        note: record.body,
        created_at: record.createdAt,
        updated_at: record.updatedAt,
        deleted: Boolean(record.deleted),
      },
      null,
      2,
    );
  }
  return files;
}

function imageRefs(values: unknown): ImageRef[] {
  if (!Array.isArray(values)) return [];
  return values
    .map((value) => {
      if (!value || typeof value !== "object") return null;
      const item = value as Record<string, unknown>;
      const fileName = String(item.file_name || item.fileName || "");
      if (!fileName) return null;
      return { fileName, label: String(item.label || ""), uri: String(item.uri || "") };
    })
    .filter((value): value is ImageRef => Boolean(value));
}

export function deserializeArchiveRecords(files: ArchiveTextFiles): ArchiveRecord[] {
  const records: ArchiveRecord[] = [];
  const entryIds = new Set<string>();
  const footprintIds = new Set<string>();
  const orderIds = new Set<string>();

  Object.keys(files).forEach((path) => {
    const entry = path.match(/^Diary\/entries\/([^/]+)\/entry\.json$/);
    if (entry) entryIds.add(entry[1]);
    const footprint = path.match(/^Diary\/footprints\/([^/]+)\/footprint\.json$/);
    if (footprint) footprintIds.add(footprint[1]);
    const order = path.match(/^Diary\/info_memos\/([^/]+)\/info_memo\.json$/);
    if (order) orderIds.add(order[1]);
  });

  for (const id of entryIds) {
    const data = parseJson(files[`Diary/entries/${id}/entry.json`]);
    records.push({
      id,
      module: "diary",
      title: String(data.title || ""),
      body: files[`Diary/entries/${id}/content.md`] || "",
      date: String(data.date || ""),
      status: "",
      type: "",
      extra: { images: imageRefs(data.images) },
      createdAt: String(data.created_at || data.createdAt || new Date().toISOString()),
      updatedAt: String(data.updated_at || data.updatedAt || new Date().toISOString()),
      deleted: Boolean(data.deleted),
    });
  }

  for (const id of footprintIds) {
    const data = parseJson(files[`Diary/footprints/${id}/footprint.json`]);
    const visits: FootprintVisit[] = [];
    const visitPrefix = `Diary/footprints/${id}/visits/`;
    Object.keys(files).forEach((path) => {
      const match = path.match(new RegExp(`^${visitPrefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^/]+)/visit\\.json$`));
      if (!match) return;
      const visitId = match[1];
      const visitData = parseJson(files[path]);
      visits.push({
        id: visitId,
        date: String(visitData.date || ""),
        thought: files[`${visitPrefix}${visitId}/thought.md`] || "",
        images: imageRefs(visitData.images),
        createdAt: String(visitData.created_at || new Date().toISOString()),
        updatedAt: String(visitData.updated_at || new Date().toISOString()),
      });
    });
    visits.sort((a, b) => b.date.localeCompare(a.date));
    records.push({
      id,
      module: "footprints",
      title: String(data.place_name || data.title || ""),
      body: files[`Diary/footprints/${id}/summary.md`] || "",
      date: String(data.date || visits[0]?.date || ""),
      status: "",
      type: "",
      extra: { visits },
      createdAt: String(data.created_at || new Date().toISOString()),
      updatedAt: String(data.updated_at || new Date().toISOString()),
      deleted: Boolean(data.deleted),
    });
  }

  for (const id of orderIds) {
    const data = parseJson(files[`Diary/info_memos/${id}/info_memo.json`]);
    const extra = data.type_fields && typeof data.type_fields === "object" ? (data.type_fields as Record<string, unknown>) : {};
    records.push({
      id,
      module: "orders",
      title: String(data.title || ""),
      body: String(data.note || data.main_content || ""),
      date: String(data.date || extra.order_date || ""),
      status: String(data.status || "在报价"),
      type: String(data.info_type || "接单记录"),
      extra,
      createdAt: String(data.created_at || new Date().toISOString()),
      updatedAt: String(data.updated_at || new Date().toISOString()),
      deleted: Boolean(data.deleted),
    });
  }

  return records;
}

export function moduleDirectory(module: ModuleKey): string {
  return module === "diary" ? "entries" : module === "footprints" ? "footprints" : "info_memos";
}
