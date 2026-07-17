import { useCallback, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Panel } from "@/components/Controls";
import { RecordRow } from "@/components/RecordRow";
import { Screen } from "@/components/Screen";
import { useRepository } from "@/db/RepositoryContext";
import type { ArchiveRecord, ModuleKey } from "@/domain/models";
import { colors, spacing } from "@/theme";

const modules: { key: ModuleKey; label: string; route: "/diary" | "/footprints" | "/orders" }[] = [
  { key: "diary", label: "日记", route: "/diary" },
  { key: "footprints", label: "足迹", route: "/footprints" },
  { key: "orders", label: "接单", route: "/orders" },
];

export default function HomeScreen() {
  const repository = useRepository();
  const router = useRouter();
  const [counts, setCounts] = useState<Record<ModuleKey, number>>({ diary: 0, footprints: 0, orders: 0 });
  const [recent, setRecent] = useState<ArchiveRecord[]>([]);

  useFocusEffect(
    useCallback(() => {
      void (async () => {
        const grouped = await Promise.all(modules.map((item) => repository.list(item.key)));
        setCounts({ diary: grouped[0].length, footprints: grouped[1].length, orders: grouped[2].length });
        setRecent(grouped.flat().sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)).slice(0, 5));
      })();
    }, [repository]),
  );

  return (
    <Screen subtitle="本地优先的个人记录" title="人生档案">
      <View style={styles.hero}>
        <Text style={styles.heroTitle}>今天也值得被保存</Text>
        <Text style={styles.heroText}>记录保存在你的设备中，导出备份由你掌握。</Text>
      </View>
      <View style={styles.metrics}>
        {modules.map((item) => (
          <Pressable key={item.key} onPress={() => router.push(item.route)} style={styles.metric}>
            <Text style={styles.count}>{counts[item.key]}</Text>
            <Text style={styles.metricLabel}>{item.label}</Text>
          </Pressable>
        ))}
      </View>
      <Text style={styles.sectionTitle}>最近更新</Text>
      <Panel>
        {recent.length ? (
          recent.map((record) => (
            <RecordRow
              key={record.id}
              meta={record.module === "diary" ? "日记" : record.module === "footprints" ? "足迹" : record.status}
              onPress={() =>
                router.push(record.module === "diary" ? "/diary" : record.module === "footprints" ? "/footprints" : "/orders")
              }
              record={record}
            />
          ))
        ) : (
          <Text style={styles.empty}>还没有记录，从底部栏目开始新建。</Text>
        )}
      </Panel>
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    minHeight: 142,
    justifyContent: "center",
    borderRadius: 8,
    padding: spacing.lg,
    backgroundColor: colors.ink,
    gap: spacing.sm,
  },
  heroTitle: { color: "#FFFFFF", fontSize: 24, fontWeight: "800" },
  heroText: { color: "#CBD1D6", lineHeight: 21 },
  metrics: { flexDirection: "row", gap: spacing.sm },
  metric: {
    flex: 1,
    minHeight: 94,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.line,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
  },
  count: { color: colors.accent, fontSize: 26, fontWeight: "800" },
  metricLabel: { color: colors.muted, marginTop: 4 },
  sectionTitle: { color: colors.ink, fontSize: 19, fontWeight: "700" },
  empty: { color: colors.muted, paddingVertical: spacing.lg, textAlign: "center" },
});
