import { useRef, useState, type PropsWithChildren } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  type TextInputProps,
  View,
  type ViewStyle,
} from "react-native";

import { colors, spacing } from "@/theme";
import { applyParagraphIndent, type TextSelection } from "@/utils/paragraphIndent";

export function PrimaryButton({
  label,
  onPress,
  disabled,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.primary, pressed && styles.pressed, disabled && styles.disabled]}
    >
      <Text style={styles.primaryText}>{label}</Text>
    </Pressable>
  );
}

export function SecondaryButton({
  label,
  onPress,
  danger,
  disabled,
}: {
  label: string;
  onPress: () => void;
  danger?: boolean;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [styles.secondary, pressed && styles.pressed, disabled && styles.disabled]}
    >
      <Text style={[styles.secondaryText, danger && { color: colors.danger }]}>{label}</Text>
    </Pressable>
  );
}

export function Field({
  label,
  multiline,
  style,
  autoParagraphIndent = false,
  onChangeText,
  onSelectionChange,
  selection: inputSelection,
  value,
  ...props
}: TextInputProps & { label: string; style?: ViewStyle; autoParagraphIndent?: boolean }) {
  const [selection, setSelection] = useState<TextSelection>({ start: 0, end: 0 });
  const selectionRef = useRef(selection);

  function updateSelection(next: TextSelection) {
    selectionRef.current = next;
    setSelection(next);
  }

  function handleChangeText(next: string) {
    if (!autoParagraphIndent || !multiline) {
      onChangeText?.(next);
      return;
    }
    const result = applyParagraphIndent(value ?? "", next, selectionRef.current);
    updateSelection(result.selection);
    onChangeText?.(result.value);
  }

  return (
    <View style={[styles.field, style]}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        multiline={multiline}
        onChangeText={handleChangeText}
        onSelectionChange={(event) => {
          const next = event.nativeEvent.selection;
          if (autoParagraphIndent && multiline) updateSelection(next);
          onSelectionChange?.(event);
        }}
        placeholderTextColor="#929AA1"
        selection={autoParagraphIndent && multiline ? selection : inputSelection}
        style={[styles.input, multiline && styles.multiline]}
        textAlignVertical={multiline ? "top" : "center"}
        value={value}
        {...props}
      />
    </View>
  );
}

export function Panel({ children }: PropsWithChildren) {
  return <View style={styles.panel}>{children}</View>;
}

export function ButtonRow({ children }: PropsWithChildren) {
  return <View style={styles.buttonRow}>{children}</View>;
}

const styles = StyleSheet.create({
  primary: {
    minHeight: 44,
    paddingHorizontal: 18,
    borderRadius: 7,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.accent,
  },
  primaryText: { color: "#FFFFFF", fontSize: 15, fontWeight: "700" },
  secondary: {
    minHeight: 42,
    paddingHorizontal: 15,
    borderRadius: 7,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
  },
  secondaryText: { color: colors.ink, fontSize: 14, fontWeight: "600" },
  pressed: { opacity: 0.7 },
  disabled: { opacity: 0.45 },
  field: { gap: spacing.xs },
  label: { color: colors.muted, fontSize: 13, fontWeight: "600" },
  input: {
    minHeight: 44,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    color: colors.ink,
    paddingHorizontal: 12,
    fontSize: 16,
  },
  multiline: { minHeight: 150, paddingTop: 12, lineHeight: 24 },
  panel: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.line,
    backgroundColor: colors.surface,
    padding: spacing.md,
    gap: spacing.md,
  },
  buttonRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
});
