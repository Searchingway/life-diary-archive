import { normalizeIncomingSystemPath } from "@/compat/incomingIntent";

export function redirectSystemPath({ path }: { path: string; initial: boolean }): string {
  return normalizeIncomingSystemPath(path);
}
