import type { ArchiveRecord, FootprintVisit } from "./models";

export interface DateRecords {
  diaries: ArchiveRecord[];
  footprints: ArchiveRecord[];
}

export function recordsForDate(records: ArchiveRecord[], selectedDate: string): DateRecords {
  return {
    diaries: records.filter((record) => record.module === "diary" && record.date === selectedDate),
    footprints: records.filter((record) => {
      if (record.module !== "footprints") return false;
      if (record.date === selectedDate) return true;
      const visits = Array.isArray(record.extra.visits) ? (record.extra.visits as FootprintVisit[]) : [];
      return visits.some((visit) => visit.date === selectedDate);
    }),
  };
}
