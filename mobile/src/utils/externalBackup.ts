export function safBackupFileStem(fileName: string): string {
  return fileName.replace(/\.zip$/i, "") || "LifeDiary-Backup";
}
