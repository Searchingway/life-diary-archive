const recentIncoming = new Map<string, number>();
const DEDUPE_WINDOW_MS = 10_000;

export function normalizeIncomingSystemPath(path: string): string {
  const value = path.trim();
  if (!/^content:\/\//i.test(value) || !/\.zip(?:$|[?#])/i.test(value)) return "/data";
  return `/data?incoming=${encodeURIComponent(value)}`;
}

export function consumeIncomingUri(uri: string, timestamp = Date.now()): boolean {
  const previous = recentIncoming.get(uri);
  recentIncoming.set(uri, timestamp);
  return previous === undefined || timestamp - previous > DEDUPE_WINDOW_MS;
}
