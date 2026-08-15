import { describe, expect, it } from "vitest";

import { applyParagraphIndent } from "../utils/paragraphIndent";

describe("applyParagraphIndent", () => {
  it("adds two full-width spaces before a first plain-text paragraph", () => {
    expect(applyParagraphIndent("", "正文", { start: 2, end: 2 })).toEqual({
      value: "　　正文",
      selection: { start: 4, end: 4 },
    });
  });

  it("adds indentation after an Enter insertion without duplicating it", () => {
    expect(applyParagraphIndent("　　第一段", "　　第一段\n", { start: 6, end: 6 })).toEqual({
      value: "　　第一段\n　　",
      selection: { start: 8, end: 8 },
    });
    expect(applyParagraphIndent("　　第一段\n　　", "　　第一段\n　　下一段", { start: 10, end: 10 })).toEqual({
      value: "　　第一段\n　　下一段",
      selection: { start: 10, end: 10 },
    });
  });

  it("preserves deletes, existing indentation, and multi-paragraph paste text", () => {
    expect(applyParagraphIndent("　　正文", "　　正", { start: 3, end: 3 })).toEqual({
      value: "　　正",
      selection: { start: 3, end: 3 },
    });
    expect(applyParagraphIndent("", "第一段\n第二段", { start: 7, end: 7 })).toEqual({
      value: "第一段\n第二段",
      selection: { start: 7, end: 7 },
    });
  });

  it("keeps an Enter selection correct when inserting in the middle of a paragraph", () => {
    expect(applyParagraphIndent("　　第一段末尾", "　　第一\n段末尾", { start: 5, end: 5 })).toEqual({
      value: "　　第一\n　　段末尾",
      selection: { start: 7, end: 7 },
    });
  });
});
