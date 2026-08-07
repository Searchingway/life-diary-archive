export type ModuleKey = "diary" | "footprints" | "orders" | "plans";

export interface ImageRef {
  fileName: string;
  uri: string;
  label: string;
}

export interface FootprintVisit {
  id: string;
  date: string;
  thought: string;
  images: ImageRef[];
  createdAt: string;
  updatedAt: string;
}

export const ORDER_STATUSES = ["在报价", "已接单", "已完成", "已验收", "已结款", "已放弃"] as const;
export type OrderStatus = (typeof ORDER_STATUSES)[number];

export interface ArchiveRecord {
  id: string;
  module: ModuleKey;
  title: string;
  body: string;
  date: string;
  status: string;
  type: string;
  extra: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  deleted?: boolean;
  deletedAt?: string;
}

export interface OrderMemo extends ArchiveRecord {
  module: "orders";
  status: OrderStatus;
}

export type NewRecord = Omit<ArchiveRecord, "id" | "createdAt" | "updatedAt" | "deleted" | "deletedAt"> & {
  id?: string;
};

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function emptyDiary(): NewRecord {
  return { module: "diary", title: "", body: "", date: today(), status: "", type: "", extra: { images: [] } };
}

export function emptyFootprint(): NewRecord {
  return { module: "footprints", title: "", body: "", date: today(), status: "", type: "", extra: { visits: [] } };
}

export function emptyOrder(): NewRecord {
  return {
    module: "orders",
    title: "",
    body: "",
    date: today(),
    status: "在报价",
    type: "接单记录",
    extra: {
      customer: "",
      intermediary: "",
      executor: "",
      orderDate: today(),
      deadline: "",
      durationDays: "",
      price: "",
      deposit: "",
      finalPayment: "",
      deliverables: "",
    },
  };
}
