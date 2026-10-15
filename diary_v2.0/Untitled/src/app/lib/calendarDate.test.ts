import { afterEach, describe, expect, it, vi } from "vitest";
import { calendarDate, calendarDays } from "./calendarDate";

afterEach(() => vi.useRealTimers());

describe("local calendar dates", () => {
  it("formats the local day at both ends of the day", () => {
    expect(calendarDate(new Date(2026, 9, 15, 0, 30))).toBe("2026-10-15");
    expect(calendarDate(new Date(2026, 9, 15, 23, 30))).toBe("2026-10-15");
  });
  it("uses today's local date by default", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 0, 1, 0, 1));
    expect(calendarDate()).toBe("2026-01-01");
  });
  it("enumerates calendar days inclusively across daylight saving changes", () => {
    expect(calendarDays("2026-03-07", "2026-03-10")).toEqual(["2026-03-07", "2026-03-08", "2026-03-09", "2026-03-10"]);
    expect(calendarDays("2026-10-31", "2026-11-03")).toEqual(["2026-10-31", "2026-11-01", "2026-11-02", "2026-11-03"]);
  });
  it("handles year boundaries and reversed ranges", () => {
    expect(calendarDays("2026-12-31", "2027-01-01")).toEqual(["2026-12-31", "2027-01-01"]);
    expect(calendarDays("2026-10-16", "2026-10-15")).toEqual([]);
  });
  it("keeps the final day when daylight saving begins at local midnight", () => {
    expect(calendarDays("2026-09-05", "2026-09-08")).toEqual(["2026-09-05", "2026-09-06", "2026-09-07", "2026-09-08"]);
  });
});
