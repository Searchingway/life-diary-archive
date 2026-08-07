import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import JSZip from "jszip";

import { deserializeArchiveRecords, serializeArchiveRecords, type ArchiveTextFiles } from "@/compat/archive";
import type { RecordRepository } from "@/db/repository";
import type { ArchiveRecord, FootprintVisit, ImageRef, ModuleKey } from "@/domain/models";
import { ensureMediaRoot, MEDIA_ROOT } from "@/services/images";

const MODULES: ModuleKey[] = ["diary", "footprints", "orders", "plans"];
const LEGACY_ROOT = `${FileSystem.documentDirectory}Diary/`;

async function allRecords(repository: RecordRepository): Promise<ArchiveRecord[]> {
  const groups = await Promise.all(MODULES.map((module) => repository.list(module)));
  return groups.flat();
}

function imageArchivePath(record: ArchiveRecord, image: ImageRef, visit?: FootprintVisit): string {
  if (record.module === "diary") return `Diary/entries/${record.id}/images/${image.fileName}`;
  return `Diary/footprints/${record.id}/visits/${visit!.id}/images/${image.fileName}`;
}

function recordImages(record: ArchiveRecord): { image: ImageRef; visit?: FootprintVisit }[] {
  if (record.module === "diary") {
    const images = Array.isArray(record.extra.images) ? (record.extra.images as ImageRef[]) : [];
    return images.map((image) => ({ image }));
  }
  if (record.module === "footprints") {
    const visits = Array.isArray(record.extra.visits) ? (record.extra.visits as FootprintVisit[]) : [];
    return visits.flatMap((visit) => visit.images.map((image) => ({ image, visit })));
  }
  return [];
}

function backupName(prefix = "人生档案"): string {
  const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14);
  return `${prefix}-${stamp}.zip`;
}

export async function createBackup(repository: RecordRepository, shouldShare = true): Promise<string> {
  const records = await allRecords(repository);
  const zip = new JSZip();
  const textFiles = serializeArchiveRecords(records);
  Object.entries(textFiles).forEach(([path, content]) => zip.file(path, content));
  zip.file(
    "manifest.json",
    JSON.stringify(
      {
        format: "life-diary-archive",
        version: 1,
        created_at: new Date().toISOString(),
        app: "人生档案 Expo 2.2.0",
        record_count: records.length,
      },
      null,
      2,
    ),
  );

  for (const record of records) {
    for (const { image, visit } of recordImages(record)) {
      const info = await FileSystem.getInfoAsync(image.uri);
      if (!info.exists) continue;
      const base64 = await FileSystem.readAsStringAsync(image.uri, { encoding: FileSystem.EncodingType.Base64 });
      zip.file(imageArchivePath(record, image, visit), base64, { base64: true });
    }
  }

  const payload = await zip.generateAsync({ type: "base64", compression: "DEFLATE", compressionOptions: { level: 6 } });
  const destination = `${FileSystem.cacheDirectory}${backupName()}`;
  await FileSystem.writeAsStringAsync(destination, payload, { encoding: FileSystem.EncodingType.Base64 });
  if (shouldShare) {
    if (!(await Sharing.isAvailableAsync())) throw new Error("当前设备不支持系统分享。");
    await Sharing.shareAsync(destination, {
      mimeType: "application/zip",
      dialogTitle: "导出人生档案备份",
      UTI: "public.zip-archive",
    });
  }
  return destination;
}

async function writeImportedImage(zip: JSZip, path: string, preferredName: string): Promise<string> {
  const entry = zip.file(path);
  if (!entry) return "";
  await ensureMediaRoot();
  const safeName = preferredName.replace(/[^a-zA-Z0-9._-]/g, "_") || `${Date.now()}.jpg`;
  let destination = `${MEDIA_ROOT}${safeName}`;
  if ((await FileSystem.getInfoAsync(destination)).exists) destination = `${MEDIA_ROOT}${Date.now()}-${safeName}`;
  const base64 = await entry.async("base64");
  await FileSystem.writeAsStringAsync(destination, base64, { encoding: FileSystem.EncodingType.Base64 });
  return destination;
}

async function hydrateImportedImages(records: ArchiveRecord[], zip: JSZip): Promise<ArchiveRecord[]> {
  for (const record of records) {
    if (record.module === "diary") {
      const images = Array.isArray(record.extra.images) ? (record.extra.images as ImageRef[]) : [];
      for (const image of images) {
        const uri = await writeImportedImage(zip, imageArchivePath(record, image), image.fileName);
        if (uri) image.uri = uri;
      }
    }
    if (record.module === "footprints") {
      const visits = Array.isArray(record.extra.visits) ? (record.extra.visits as FootprintVisit[]) : [];
      for (const visit of visits) {
        for (const image of visit.images) {
          const uri = await writeImportedImage(zip, imageArchivePath(record, image, visit), image.fileName);
          if (uri) image.uri = uri;
        }
      }
    }
  }
  return records;
}

async function importZipUri(repository: RecordRepository, uri: string): Promise<number> {
  const base64 = await FileSystem.readAsStringAsync(uri, { encoding: FileSystem.EncodingType.Base64 });
  const zip = await JSZip.loadAsync(base64, { base64: true });
  const textFiles: ArchiveTextFiles = {};
  const textEntries = Object.values(zip.files).filter(
    (entry) => !entry.dir && /\.(json|md|txt)$/i.test(entry.name) && entry.name !== "manifest.json",
  );
  for (const entry of textEntries) textFiles[entry.name] = await entry.async("string");
  const records = await hydrateImportedImages(deserializeArchiveRecords(textFiles), zip);
  if (!records.length) throw new Error("备份包中没有可识别的日记、足迹、接单或计划记录。");
  await repository.replaceAll(records);
  return records.length;
}

export async function pickAndRestoreBackup(repository: RecordRepository): Promise<number | null> {
  const picked = await DocumentPicker.getDocumentAsync({
    type: ["application/zip", "application/octet-stream"],
    copyToCacheDirectory: true,
  });
  if (picked.canceled || !picked.assets[0]) return null;
  await createBackup(repository, false);
  return importZipUri(repository, picked.assets[0].uri);
}

async function collectLegacyFiles(directory: string, relative = "Diary"): Promise<ArchiveTextFiles> {
  const files: ArchiveTextFiles = {};
  const names = await FileSystem.readDirectoryAsync(directory);
  for (const name of names) {
    const uri = `${directory}${name}`;
    const path = `${relative}/${name}`;
    const info = await FileSystem.getInfoAsync(uri);
    if (!info.exists) continue;
    if (info.isDirectory) Object.assign(files, await collectLegacyFiles(`${uri}/`, path));
    else if (/\.(json|md|txt)$/i.test(name)) files[path] = await FileSystem.readAsStringAsync(uri);
  }
  return files;
}

function legacyImageCandidates(record: ArchiveRecord, image: ImageRef, visit?: FootprintVisit): string[] {
  if (record.module === "diary") return [`${LEGACY_ROOT}entries/${record.id}/images/${image.fileName}`, image.uri];
  return [`${LEGACY_ROOT}footprints/${record.id}/visits/${visit!.id}/images/${image.fileName}`, image.uri];
}

async function copyLegacyImages(records: ArchiveRecord[]): Promise<void> {
  await ensureMediaRoot();
  for (const record of records) {
    for (const { image, visit } of recordImages(record)) {
      for (const candidate of legacyImageCandidates(record, image, visit)) {
        if (!candidate) continue;
        const info = await FileSystem.getInfoAsync(candidate);
        if (!info.exists || info.isDirectory) continue;
        let destination = `${MEDIA_ROOT}${image.fileName}`;
        if ((await FileSystem.getInfoAsync(destination)).exists) destination = `${MEDIA_ROOT}${Date.now()}-${image.fileName}`;
        await FileSystem.copyAsync({ from: candidate, to: destination });
        image.uri = destination;
        break;
      }
    }
  }
}

export async function legacyArchiveExists(): Promise<boolean> {
  return (await FileSystem.getInfoAsync(LEGACY_ROOT)).exists;
}

export async function importLegacyArchive(repository: RecordRepository): Promise<number> {
  if (!(await legacyArchiveExists())) throw new Error("未检测到旧版 Qt 的 Diary 数据目录。");
  await createBackup(repository, false);
  const files = await collectLegacyFiles(LEGACY_ROOT);
  const records = deserializeArchiveRecords(files);
  if (!records.length) throw new Error("旧版目录存在，但没有识别到可导入记录。");
  await copyLegacyImages(records);
  await repository.replaceAll(records);
  return records.length;
}
