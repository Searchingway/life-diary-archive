import { Pressable, StyleSheet, Text, View } from "react-native";

import type { ArchiveRecord } from "@/domain/models";
import { colors, spacing } from "@/theme";

export function RecordRow({
  record,
  meta,
  onPress,
}: {
  record: ArchiveRecord;
  meta?: string;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.row, pressed && styles.pressed]}>
      <View style={styles.body}>
        <Text numberOfLines={1} style={styles.title}>
          {record.title || "未命名记录"}
        </Text>
        <Text numberOfLines={1} style={styles.meta}>
          {[record.date, meta].filter(Boolean).join(" · ")}
        </Text>
      </View>
      <Text style={styles.arrow}>›</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: 68,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.line,
    paddingVertical: spacing.sm,
    flexDirection: "row",
    alignItems: "center",
  },
  body: { flex: 1, gap: 5 },
  title: { color: colors.ink, fontSize: 17, fontWeight: "600" },
  meta: { color: colors.muted, fontSize: 13 },
  arrow: { color: colors.muted, fontSize: 27, paddingLeft: spacing.sm },
  pressed: { opacity: 0.58 },
});
