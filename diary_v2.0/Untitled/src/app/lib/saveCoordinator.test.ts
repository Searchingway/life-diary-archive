import { describe, expect, it } from "vitest";
import { SaveCoordinator, shouldApplySaveResult, shouldPersistDiary } from "./saveCoordinator";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve;
    reject = nextReject;
  });
  return { promise, resolve, reject };
}

describe("SaveCoordinator", () => {
  it("runs save requests strictly in enqueue order", async () => {
    const coordinator = new SaveCoordinator();
    const first = deferred<void>();
    const started: string[] = [];

    const firstSave = coordinator.enqueue(async () => {
      started.push("A");
      await first.promise;
    });
    const secondSave = coordinator.enqueue(async () => {
      started.push("B");
    });
    const thirdSave = coordinator.enqueue(async () => {
      started.push("C");
    });

    await Promise.resolve();
    expect(started).toEqual(["A"]);
    first.resolve();
    await Promise.all([firstSave, secondSave, thirdSave]);
    expect(started).toEqual(["A", "B", "C"]);
  });

  it("continues with the next save after a failed save", async () => {
    const coordinator = new SaveCoordinator();
    const started: string[] = [];

    const failedSave = coordinator.enqueue(async () => {
      started.push("failed");
      throw new Error("network failed");
    });
    const nextSave = coordinator.enqueue(async () => {
      started.push("next");
    });

    await expect(failedSave).rejects.toThrow("network failed");
    await nextSave;
    expect(started).toEqual(["failed", "next"]);
  });

  it("does not apply an old response after a newer edit or record switch", () => {
    expect(shouldApplySaveResult("entry-a", 5, "entry-a", 4)).toBe(false);
    expect(shouldApplySaveResult("entry-b", 4, "entry-a", 4)).toBe(false);
    expect(shouldApplySaveResult("entry-a", 4, "entry-a", 4)).toBe(true);
  });

  it("preserves the newest queued snapshot after an earlier save completes", async () => {
    const coordinator = new SaveCoordinator();
    const first = deferred<void>();
    const persisted: string[] = [];

    const firstSave = coordinator.enqueue(async () => {
      await first.promise;
      persisted.push("A");
    });
    const latestSave = coordinator.enqueue(async () => {
      persisted.push("B");
    });

    first.resolve();
    await Promise.all([firstSave, latestSave]);
    expect(persisted).toEqual(["A", "B"]);
  });

  it("does not continue a record switch when its required save fails", async () => {
    const coordinator = new SaveCoordinator();
    let switched = false;

    try {
      await coordinator.enqueue(async () => {
        throw new Error("save failed");
      });
      switched = true;
    } catch {
      // The caller remains on the current record after a rejected save.
    }

    expect(switched).toBe(false);
  });

  it("skips a blank new draft but persists an existing diary cleared to empty", () => {
    expect(shouldPersistDiary({ id: "", title: "", body: "" })).toBe(false);
    expect(shouldPersistDiary({ id: "entry-a", title: "", body: "" })).toBe(true);
  });
});
