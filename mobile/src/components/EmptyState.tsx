import { StyleSheet, Text, View } from "react-native";

import { colors } from "@/theme";

export function EmptyState({ text }: { text: string }) {
  return (
    <View style={styles.root}>
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { paddingVertical: 46, alignItems: "center" },
  text: { color: colors.muted, fontSize: 15 },
});
