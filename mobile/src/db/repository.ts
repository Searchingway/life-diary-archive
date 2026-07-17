import type { SQLiteDatabase } from "expo-sqlite";

import type { ArchiveRecord, ModuleKey, NewRecord } from "../domain/models";

export interface RecordRepository {
  list(module: ModuleKey, query?: string): Promise<ArchiveRecord[]>;
  get(id: string, includeDeleted?: boolean): Promise<ArchiveRecord | null>;
  save(record: NewRecord): Promise<ArchiveRecord>;
  softDelete(id: string): Promise<void>;
  count(module: ModuleKey): Promise<number>;
  replaceAll(records: ArchiveRecord[]): Promise<void>;
}

function now(): string {
  return new Date().toISOString();
}

function makeId(): string {
  const random = Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
  return `${Date.now().toString(16)}${random}`.slice(0, 32);
}

function normalize(record: NewRecord, existing?: ArchiveRecord | null): ArchiveRecord {
  const timestamp = now();
  return {
    id: record.id || existing?.id || makeId(),
    module: record.module,
    title: record.title.trim(),
    body: record.body,
    date: record.date,
    status: record.status,
    type: record.type,
    extra: record.extra ?? {},
    createdAt: existing?.createdAt || timestamp,
    updatedAt: timestamp,
    deleted: false,
  };
}

export function createMemoryRecordRepository(): RecordRepository {
  const records = new Map<string, ArchiveRecord>();
  return {
    async list(module, query = "") {
      const keyword = query.trim().toLocaleLowerCase();
      return [...records.values()]
        .filter((record) => record.module === module && !record.deleted)
        .filter((record) => {
          if (!keyword) return true;
          return `${record.title}\n${record.body}\n${record.status}\n${record.type}\n${JSON.stringify(record.extra)}`
            .toLocaleLowerCase()
            .includes(keyword);
        })
        .sort((a, b) => Date.parse(b.date || b.updatedAt) - Date.parse(a.date || a.updatedAt));
    },
    async get(id, includeDeleted = false) {
      const record = records.get(id) ?? null;
      if (record?.deleted && !includeDeleted) return null;
      return record;
    },
    async save(input) {
      const record = normalize(input, input.id ? records.get(input.id) : null);
      records.set(record.id, record);
      return record;
    },
    async softDelete(id) {
      const record = records.get(id);
      if (!record) throw new Error("找不到要删除的记录");
      records.set(id, { ...record, deleted: true, deletedAt: now(), updatedAt: now() });
    },
    async count(module) {
      return [...records.values()].filter((record) => record.module === module && !record.deleted).length;
    },
    async replaceAll(nextRecords) {
      records.clear();
      nextRecords.forEach((record) => records.set(record.id, record));
    },
  };
}

type RecordRow = {
  id: string;
  module: ModuleKey;
  title: string;
  body: string;
  date: string;
  status: string;
  type: string;
  extra_json: string;
  created_at: string;
  updated_at: string;
  deleted: number;
  deleted_at: string | null;
};

function fromRow(row: RecordRow): ArchiveRecord {
  return {
    id: row.id,
    module: row.module,
    title: row.title,
    body: row.body,
    date: row.date,
    status: row.status,
    type: row.type,
    extra: JSON.parse(row.extra_json || "{}"),
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    deleted: Boolean(row.deleted),
    deletedAt: row.deleted_at || undefined,
  };
}

export function createSqliteRecordRepository(database: SQLiteDatabase): RecordRepository {
  return {
    async list(module, query = "") {
      const keyword = `%${query.trim().toLocaleLowerCase()}%`;
      const rows = await database.getAllAsync<RecordRow>(
        `SELECT * FROM records
         WHERE module = ? AND deleted = 0
           AND (? = '%%' OR lower(title || char(10) || body || char(10) || status || char(10) || type || char(10) || extra_json) LIKE ?)
         ORDER BY date DESC, updated_at DESC`,
        module,
        keyword,
        keyword,
      );
      return rows.map(fromRow);
    },
    async get(id, includeDeleted = false) {
      const row = await database.getFirstAsync<RecordRow>(
        `SELECT * FROM records WHERE id = ? ${includeDeleted ? "" : "AND deleted = 0"}`,
        id,
      );
      return row ? fromRow(row) : null;
    },
    async save(input) {
      const existing = input.id ? await this.get(input.id, true) : null;
      const record = normalize(input, existing);
      await database.runAsync(
        `INSERT INTO records
          (id, module, title, body, date, status, type, extra_json, created_at, updated_at, deleted, deleted_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
         ON CONFLICT(id) DO UPDATE SET
          module=excluded.module, title=excluded.title, body=excluded.body, date=excluded.date,
          status=excluded.status, type=excluded.type, extra_json=excluded.extra_json,
          updated_at=excluded.updated_at, deleted=0, deleted_at=NULL`,
        record.id,
        record.module,
        record.title,
        record.body,
        record.date,
        record.status,
        record.type,
        JSON.stringify(record.extra),
        record.createdAt,
        record.updatedAt,
      );
      return record;
    },
    async softDelete(id) {
      const timestamp = now();
      const result = await database.runAsync(
        "UPDATE records SET deleted=1, deleted_at=?, updated_at=? WHERE id=?",
        timestamp,
        timestamp,
        id,
      );
      if (!result.changes) throw new Error("找不到要删除的记录");
    },
    async count(module) {
      const row = await database.getFirstAsync<{ count: number }>(
        "SELECT COUNT(*) AS count FROM records WHERE module=? AND deleted=0",
        module,
      );
      return row?.count ?? 0;
    },
    async replaceAll(records) {
      await database.withTransactionAsync(async () => {
        await database.runAsync("DELETE FROM records");
        for (const record of records) {
          await database.runAsync(
            `INSERT INTO records
              (id, module, title, body, date, status, type, extra_json, created_at, updated_at, deleted, deleted_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            record.id,
            record.module,
            record.title,
            record.body,
            record.date,
            record.status,
            record.type,
            JSON.stringify(record.extra),
            record.createdAt,
            record.updatedAt,
            record.deleted ? 1 : 0,
            record.deletedAt ?? null,
          );
        }
      });
    },
  };
}
