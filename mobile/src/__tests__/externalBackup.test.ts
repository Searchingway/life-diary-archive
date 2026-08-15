import { describe, expect, it } from "vitest";

import { safBackupFileStem } from "../utils/externalBackup";

describe("external backup helpers", () => {
  it("keeps the timestamped name but removes only the ZIP extension for SAF", () => {
    expect(safBackupFileStem("人生档案-20260815.zip")).toBe("人生档案-20260815");
    expect(safBackupFileStem("backup.ZIP")).toBe("backup");
  });
});
