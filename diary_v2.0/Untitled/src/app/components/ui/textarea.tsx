import * as React from "react";

import { cn } from "./utils";

type TextareaProps = React.ComponentProps<"textarea"> & {
  autoParagraphIndent?: boolean;
  paragraphIndent?: string;
};

function Textarea({
  className,
  autoParagraphIndent = false,
  paragraphIndent = "　　",
  onChange,
  onKeyDown,
  ...props
}: TextareaProps) {
  function handleChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    const value = event.currentTarget.value;
    const previousValue = typeof props.value === "string" ? props.value : "";
    if (autoParagraphIndent && previousValue.length === 0 && value.length > 0 && !value.startsWith(paragraphIndent)) {
      const cursor = event.currentTarget.selectionStart + paragraphIndent.length;
      event.currentTarget.value = `${paragraphIndent}${value}`;
      event.currentTarget.setSelectionRange(cursor, cursor);
    }
    onChange?.(event);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    onKeyDown?.(event);
    if (
      event.defaultPrevented ||
      !autoParagraphIndent ||
      event.key !== "Enter" ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.nativeEvent.isComposing ||
      props.readOnly ||
      props.disabled
    ) {
      return;
    }

    event.preventDefault();
    event.currentTarget.setRangeText(
      `\n${paragraphIndent}`,
      event.currentTarget.selectionStart,
      event.currentTarget.selectionEnd,
      "end",
    );
    event.currentTarget.dispatchEvent(new Event("input", { bubbles: true }));
  }

  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "resize-none border-input placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 flex field-sizing-content min-h-16 w-full rounded-md border bg-input-background px-3 py-2 text-base transition-[color,box-shadow] outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        className,
      )}
      {...props}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
    />
  );
}

export { Textarea };
