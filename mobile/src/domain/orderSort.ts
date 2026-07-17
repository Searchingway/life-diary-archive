import type { OrderMemo } from "./models";

const STATUS_PRIORITY: Record<string, number> = {
  已接单: 0,
  进行中: 0,
  已验收: 1,
  在报价: 2,
  已完成: 3,
  已结款: 4,
  已放弃: 5,
};

export function sortOrderMemos<T extends Pick<OrderMemo, "status" | "date" | "updatedAt">>(records: T[]): T[] {
  return [...records].sort((a, b) => {
    const priority = (STATUS_PRIORITY[a.status] ?? 9) - (STATUS_PRIORITY[b.status] ?? 9);
    if (priority !== 0) return priority;
    return Date.parse(b.date || b.updatedAt) - Date.parse(a.date || a.updatedAt);
  });
}
