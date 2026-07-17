import { openDatabaseAsync } from "expo-sqlite";

import { CREATE_SCHEMA_SQL, DATABASE_NAME, SCHEMA_VERSION } from "./schema";
import { createSqliteRecordRepository } from "./repository";

let databasePromise: ReturnType<typeof openDatabaseAsync> | null = null;

export async function getDatabase() {
  databasePromise ??= openDatabaseAsync(DATABASE_NAME);
  return databasePromise;
}

export async function initializeDatabase() {
  const database = await getDatabase();
  await database.execAsync(CREATE_SCHEMA_SQL);
  await database.runAsync(
    "INSERT INTO app_meta(key, value) VALUES('schema_version', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
    String(SCHEMA_VERSION),
  );
  return database;
}

export async function getRecordRepository() {
  return createSqliteRecordRepository(await initializeDatabase());
}
