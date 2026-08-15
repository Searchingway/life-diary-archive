export type TextSelection = { start: number; end: number };

export type ParagraphIndentResult = {
  value: string;
  selection: TextSelection;
};

const INDENT = "　　";

function insertedText(previous: string, next: string): { start: number; text: string } {
  let start = 0;
  while (start < previous.length && start < next.length && previous[start] === next[start]) start += 1;

  let previousEnd = previous.length;
  let nextEnd = next.length;
  while (previousEnd > start && nextEnd > start && previous[previousEnd - 1] === next[nextEnd - 1]) {
    previousEnd -= 1;
    nextEnd -= 1;
  }
  return { start, text: next.slice(start, nextEnd) };
}

export function applyParagraphIndent(previous: string, next: string, selection: TextSelection): ParagraphIndentResult {
  const safeSelection = {
    start: Math.max(0, Math.min(selection.start, next.length)),
    end: Math.max(0, Math.min(selection.end, next.length)),
  };

  if (!previous && next && !next.includes("\n") && !/^\s/.test(next)) {
    return {
      value: `${INDENT}${next}`,
      selection: { start: safeSelection.start + INDENT.length, end: safeSelection.end + INDENT.length },
    };
  }

  const inserted = insertedText(previous, next);
  if (inserted.text !== "\n" || next.slice(inserted.start + 1).startsWith(INDENT)) {
    return { value: next, selection: safeSelection };
  }

  const value = `${next.slice(0, inserted.start + 1)}${INDENT}${next.slice(inserted.start + 1)}`;
  return {
    value,
    selection: { start: safeSelection.start + INDENT.length, end: safeSelection.end + INDENT.length },
  };
}
