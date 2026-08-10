import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import JSZip from "jszip";

import { deserializeArchiveRecords, serializeArchiveRecords, type ArchiveTextFiles } from "@/compat/archive";
import { createMobileSnapshotManifest, parseDesktopCanonicalTextFiles, validateArchivePaths, type ProtocolManifest } from "@/compat/syncProtocol";
import type { RecordRepository } from "@/db/repository";
import type { ArchiveRecord, FootprintVisit, ImageRef, ModuleKey } from "@/domain/models";
import { copyImageIntoMedia, ensureMediaRoot, MEDIA_ROOT } from "@/services/images";

const MODULES: ModuleKey[] = ["diary", "footprints", "orders", "plans"];
const LEGACY_ROOT = `${FileSystem.documentDirectory}Diary/`;

async function allRecords(repository: RecordRepository): Promise<ArchiveRecord[]> {
  const groups = await Promise.all(MODULES.map((module) => repository.list(module)));
  return groups.flat();
}

function imageArchivePath(record: ArchiveRecord, image: ImageRef, visit?: FootprintVisit): string {
  if (record.module === "diary") return `Diary/entries/${record.id}/images/${image.fileName}`;
  if (!visit) return `Diary/footprints/${record.id}/images/${image.fileName}`;
  return `Diary/footprints/${record.id}/visits/${visit!.id}/images/${image.fileName}`;
}

function recordImages(record: ArchiveRecord): { image: ImageRef; visit?: FootprintVisit }[] {
  if (record.module === "diary") {
    const images = Array.isArray(record.extra.images) ? (record.extra.images as ImageRef[]) : [];
    return images.map((image) => ({ image }));
  }
  if (record.module === "footprints") {
    const visits = Array.isArray(record.extra.visits) ? (record.extra.visits as FootprintVisit[]) : [];
    const images = Array.isArray(record.extra.images) ? (record.extra.images as ImageRef[]) : [];
    return [...images.map((image) => ({ image })), ...visits.flatMap((visit) => visit.images.map((image) => ({ image, visit })))];
  }
  return [];
}

function backupName(prefix = "人生档案"): string {
  const stamp = new Date().toISOString().replace(/[-:T]/g, "").slice(0, 14);
  return `${prefix}-${stamp}.zip`;
}

async function writeArchive(repository: RecordRepository, manifest: Record<string, unknown>, prefix: string, shouldShare: boolean): Promise<string> {
  const records = await allRecords(repository);
  const zip = new JSZip();
  const textFiles = serializeArchiveRecords(records);
  Object.entries(textFiles).forEach(([path, content]) => zip.file(path, content));
  zip.file("manifest.json", JSON.stringify({ ...manifest, record_count: records.length }, null, 2));

  for (const record of records) {
    for (const { image, visit } of recordImages(record)) {
      const info = await FileSystem.getInfoAsync(image.uri);
      if (!info.exists) continue;
      const base64 = await FileSystem.readAsStringAsync(image.uri, { encoding: FileSystem.EncodingType.Base64 });
      zip.file(imageArchivePath(record, image, visit), base64, { base64: true });
    }
  }

  const payload = await zip.generateAsync({ type: "base64", compression: "DEFLATE", compressionOptions: { level: 6 } });
  const destination = `${FileSystem.cacheDirectory}${backupName(prefix)}`;
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

export async function createBackup(repository: RecordRepository, shouldShare = true, prefix = "人生档案"): Promise<string> {
  return writeArchive(repository, {
    format: "life-diary-archive",
    version: 1,
    created_at: new Date().toISOString(),
    app: "人生档案 Expo 2.3.0",
  }, prefix, shouldShare);
}

export async function createMobileSnapshot(repository: RecordRepository, shouldShare = true): Promise<string> {
  return writeArchive(repository, createMobileSnapshotManifest(), "LifeDiary-Mobile-Snapshot", shouldShare);
}

async function writeImportedImage(zip: JSZip, path: string, preferredName: string, root = MEDIA_ROOT): Promise<string> {
  const entry = zip.file(path);
  if (!entry) return "";
  await FileSystem.makeDirectoryAsync(root, { intermediates: true });
  const safeName = preferredName.replace(/[^a-zA-Z0-9._-]/g, "_") || `${Date.now()}.jpg`;
  let destination = `${root}${safeName}`;
  if ((await FileSystem.getInfoAsync(destination)).exists) destination = `${MEDIA_ROOT}${Date.now()}-${safeName}`;
  const base64 = await entry.async("base64");
  await FileSystem.writeAsStringAsync(destination, base64, { encoding: FileSystem.EncodingType.Base64 });
  return destination;
}

async function hydrateImportedImages(records: ArchiveRecord[], zip: JSZip, root = MEDIA_ROOT): Promise<ArchiveRecord[]> {
  for (const record of records) {
    if (record.module === "diary") {
      const images = Array.isArray(record.extra.images) ? (record.extra.images as ImageRef[]) : [];
      for (const image of images) {
        const uri = await writeImportedImage(zip, imageArchivePath(record, image), image.fileName, root);
        if (uri) image.uri = uri;
      }
    }
    if (record.module === "footprints") {
      const placeImages = Array.isArray(record.extra.images) ? (record.extra.images as ImageRef[]) : [];
      for (const image of placeImages) {
        const uri = await writeImportedImage(zip, imageArchivePath(record, image), image.fileName, root);
        if (uri) image.uri = uri;
      }
      const visits = Array.isArray(record.extra.visits) ? (record.extra.visits as FootprintVisit[]) : [];
      for (const visit of visits) {
        for (const image of visit.images) {
          const uri = await writeImportedImage(zip, imageArchivePath(record, image, visit), image.fileName, root);
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

export type DesktopCanonicalImport = {
  manifest: ProtocolManifest;
  records: ArchiveRecord[];
  zip: JSZip;
  preview: Record<ModuleKey, number>;
};

async function loadZip(uri: string): Promise<JSZip> {
  let cachedUri = "";
  if (uri.startsWith("content://")) {
    cachedUri = `${FileSystem.cacheDirectory}DesktopCanonicalIncoming-${Date.now()}.zip`;
    await FileSystem.copyAsync({ from: uri, to: cachedUri });
  }
  let base64 = "";
  try {
    base64 = await FileSystem.readAsStringAsync(cachedUri || uri, { encoding: FileSystem.EncodingType.Base64 });
  } finally {
    if (cachedUri) await FileSystem.deleteAsync(cachedUri, { idempotent: true });
  }
  if (!base64.startsWith("UEs")) throw new Error("Selected file is not a ZIP archive");
  const zip = await JSZip.loadAsync(base64, { base64: true });
  const paths = Object.values(zip.files).filter((entry) => !entry.dir).map((entry) => entry.name);
  validateArchivePaths(paths);
  let totalTextBytes = 0;
  for (const entry of Object.values(zip.files)) {
    if (entry.dir || !/\.(json|md)$/i.test(entry.name)) continue;
    const content = await entry.async("string");
    totalTextBytes += content.length;
    if (totalTextBytes > 20 * 1024 * 1024) throw new Error("Sync archive text content is unreasonably large");
  }
  return zip;
}

function requireImageFiles(records: ArchiveRecord[], zip: JSZip): void {
  for (const record of records) {
    for (const { image, visit } of recordImages(record)) {
      if (!zip.file(imageArchivePath(record, image, visit))) throw new Error(`Sync archive is missing image ${image.fileName}`);
    }
  }
}

async function protocolTextFiles(zip: JSZip): Promise<ArchiveTextFiles> {
  const files: ArchiveTextFiles = {};
  for (const entry of Object.values(zip.files)) {
    if (!entry.dir && (entry.name === "manifest.json" || /\.(json|md)$/i.test(entry.name))) files[entry.name] = await entry.async("string");
  }
  return files;
}

export async function loadDesktopCanonicalImport(uri: string): Promise<DesktopCanonicalImport> {
  const zip = await loadZip(uri);
  const parsed = parseDesktopCanonicalTextFiles(await protocolTextFiles(zip));
  requireImageFiles(parsed.records, zip);
  const preview: Record<ModuleKey, number> = { diary: 0, footprints: 0, plans: 0, orders: 0 };
  parsed.records.filter((record) => !record.deleted).forEach((record) => { preview[record.module] += 1; });
  return { ...parsed, zip, preview };
}

async function promoteHydratedImages(records: ArchiveRecord[]): Promise<void> {
  for (const record of records) {
    for (const { image } of recordImages(record)) {
      if (image.uri) image.uri = await copyImageIntoMedia(image.uri, image.fileName);
    }
  }
}

async function verifySharedReplacement(repository: RecordRepository, records: ArchiveRecord[]): Promise<void> {
  for (const module of MODULES) {
    const expected = records.filter((record) => record.module === module && !record.deleted).map((record) => record.id).sort();
    const actual = (await repository.list(module)).map((record) => record.id).sort();
    if (JSON.stringify(expected) !== JSON.stringify(actual)) throw new Error(`Desktop sync verification failed for ${module}`);
  }
}

export async function applyDesktopCanonicalImport(repository: RecordRepository, prepared: DesktopCanonicalImport): Promise<{ count: number; safetyBackup: string }> {
  const temporaryRoot = `${FileSystem.cacheDirectory}DesktopCanonicalIncoming-${Date.now()}/`;
  const previous = (await allRecords(repository)).filter((record) => MODULES.includes(record.module));
  try {
    const hydrated = await hydrateImportedImages(prepared.records, prepared.zip, temporaryRoot);
    const safetyBackup = await createBackup(repository, false, "BeforeDesktopSync");
    if (!safetyBackup) throw new Error("Desktop sync safety backup was not created");
    await repository.replaceSharedModules(hydrated);
    try {
      await promoteHydratedImages(hydrated);
      await verifySharedReplacement(repository, hydrated);
    } catch (error) {
      await repository.replaceSharedModules(previous);
      throw error;
    }
    return { count: hydrated.filter((record) => !record.deleted).length, safetyBackup };
  } finally {
    await FileSystem.deleteAsync(temporaryRoot, { idempotent: true });
  }
}

export async function pickDesktopCanonicalImport(): Promise<DesktopCanonicalImport | null> {
  const picked = await DocumentPicker.getDocumentAsync({ type: ["application/zip", "application/x-zip-compressed"], copyToCacheDirectory: true });
  if (picked.canceled || !picked.assets[0]) return null;
  return loadDesktopCanonicalImport(picked.assets[0].uri);
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
