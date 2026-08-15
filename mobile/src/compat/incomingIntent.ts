const recentIncoming = new Map<string, number>();
const DEDUPE_WINDOW_MS = 10_000;

export function normalizeIncomingSystemPath(path: string): string {
  const value = path.trim();
  if (/^content:\/\//i.test(value)) {
    return /\.zip(?:$|[?#])/i.test(value) ? `/data?incoming=${encodeURIComponent(value)}` : "/";
  }
  return value.startsWith("/") && !value.startsWith("//") ? value : "/";
}

export function consumeIncomingUri(uri: string, timestamp = Date.now()): boolean {
  const previous = recentIncoming.get(uri);
  recentIncoming.set(uri, timestamp);
  return previous === undefined || timestamp - previous > DEDUPE_WINDOW_MS;
}
