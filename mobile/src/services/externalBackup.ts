import * as FileSystem from "expo-file-system/legacy";

import type { RecordRepository } from "@/db/repository";
import { safBackupFileStem } from "@/utils/externalBackup";

export const EXTERNAL_BACKUP_DIRECTORY_KEY = "external_backup_directory_uri";

export async function getExternalBackupDirectory(repository: RecordRepository): Promise<string | null> {
  return repository.getMeta(EXTERNAL_BACKUP_DIRECTORY_KEY);
}

export async function selectExternalBackupDirectory(repository: RecordRepository): Promise<string | null> {
  const permission = await FileSystem.StorageAccessFramework.requestDirectoryPermissionsAsync();
  if (!permission.granted || !permission.directoryUri) return null;
  await repository.setMeta(EXTERNAL_BACKUP_DIRECTORY_KEY, permission.directoryUri);
  return permission.directoryUri;
}

export async function clearExternalBackupDirectory(repository: RecordRepository): Promise<void> {
  await repository.setMeta(EXTERNAL_BACKUP_DIRECTORY_KEY, null);
}

export async function copyZipToExternalBackupDirectory(directoryUri: string, sourceZip: string): Promise<string> {
  const fileName = sourceZip.split("/").pop() || "LifeDiary-Backup.zip";
  const target = await FileSystem.StorageAccessFramework.createFileAsync(directoryUri, safBackupFileStem(fileName), "application/zip");
  const payload = await FileSystem.readAsStringAsync(sourceZip, { encoding: FileSystem.EncodingType.Base64 });
  await FileSystem.writeAsStringAsync(target, payload, { encoding: FileSystem.EncodingType.Base64 });
  return target;
}
