export class SaveCoordinator {
  private tail: Promise<void> = Promise.resolve();
  private pending = 0;

  constructor(private readonly onPendingChange?: (pending: boolean) => void) {}

  enqueue<T>(operation: () => Promise<T>): Promise<T> {
    this.pending += 1;
    this.onPendingChange?.(true);
    const result = this.tail.then(operation);
    this.tail = result.then(
      () => undefined,
      () => undefined,
    );
    return result.finally(() => {
      this.pending -= 1;
      this.onPendingChange?.(this.pending > 0);
    });
  }

  get hasPendingSaves() {
    return this.pending > 0;
  }
}

export function shouldApplySaveResult(
  currentRecordId: string,
  currentRevision: number,
  savingRecordId: string,
  savingRevision: number,
) {
  return currentRecordId === savingRecordId && currentRevision === savingRevision;
}

export function shouldPersistDiary(record: { id: string; title: string; body: string }) {
  return Boolean(record.id || record.title.trim() || record.body.trim());
}
