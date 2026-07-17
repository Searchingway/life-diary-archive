import { StyleSheet, Text, View } from "react-native";

import { colors } from "@/theme";

export function StatusBanner({ text, error }: { text: string; error?: boolean }) {
  if (!text) return null;
  return (
    <View style={[styles.banner, error && styles.error]}>
      <Text style={[styles.text, error && styles.errorText]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: { borderRadius: 7, padding: 11, backgroundColor: colors.accentSoft },
  error: { backgroundColor: "#F8E3E3" },
  text: { color: colors.accent, lineHeight: 20 },
  errorText: { color: colors.danger },
});
