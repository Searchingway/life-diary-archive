import { describe, expect, it } from "vitest";

import { sortOrderMemos } from "../domain/orderSort";
import type { OrderMemo } from "../domain/models";

function order(id: string, status: OrderMemo["status"], date: string): OrderMemo {
  return {
    id,
    module: "orders",
    title: id,
    body: "",
    date,
    status,
    type: "接单记录",
    extra: {},
    createdAt: `${date}T00:00:00.000Z`,
    updatedAt: `${date}T00:00:00.000Z`,
  };
}

describe("sortOrderMemos", () => {
  it("puts accepted active work first and sorts each status newest first", () => {
    const result = sortOrderMemos([
      order("paid", "已结款", "2026-06-23"),
      order("accepted-old", "已接单", "2026-06-01"),
      order("accepted-new", "已接单", "2026-06-20"),
      order("accepted-unpaid", "已验收", "2026-06-22"),
      order("quote", "在报价", "2026-06-23"),
      order("abandoned", "已放弃", "2026-06-23"),
    ]);

    expect(result.map((item) => item.id)).toEqual([
      "accepted-new",
      "accepted-old",
      "accepted-unpaid",
      "quote",
      "paid",
      "abandoned",
    ]);
  });
});
