import { useCallback, useMemo, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Panel } from "@/components/Controls";
import { RecordRow } from "@/components/RecordRow";
import { Screen } from "@/components/Screen";
import { useRepository } from "@/db/RepositoryContext";
import type { ArchiveRecord } from "@/domain/models";
import { today } from "@/domain/models";
import { selectTodayPlanTasks, type PlanMemo, type TodayPlanTask } from "@/domain/plans";
import { recordsForDate } from "@/domain/today";
import { colors, spacing } from "@/theme";

const modules: { key: "diary" | "footprints" | "plans"; label: string; route: "/diary" | "/footprints" | "/plans" }[] = [
  { key: "diary", label: "日记", route: "/diary" },
  { key: "footprints", label: "足迹", route: "/footprints" },
  { key: "plans", label: "进行中计划", route: "/plans" },
];

function changeDate(value: string, offset: number): string {
  const date = new Date(`${value}T12:00:00`);
  date.setDate(date.getDate() + offset);
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");
}

export default function HomeScreen() {
  const repository = useRepository();
  const router = useRouter();
  const [counts, setCounts] = useState({ diary: 0, footprints: 0, plans: 0 });
  const [recent, setRecent] = useState<ArchiveRecord[]>([]);
  const [records, setRecords] = useState<ArchiveRecord[]>([]);
  const [selectedDate, setSelectedDate] = useState(today());

  useFocusEffect(
    useCallback(() => {
      void (async () => {
        const grouped = await Promise.all(modules.map((item) => repository.list(item.key)));
        const all = grouped.flat();
        setCounts({ diary: grouped[0].length, footprints: grouped[1].length, plans: grouped[2].filter((record) => record.status === "进行中").length });
        setRecords(all);
        setRecent(all.sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)).slice(0, 5));
      })();
    }, [repository]),
  );

  const daily = useMemo(() => recordsForDate(records, selectedDate), [records, selectedDate]);
  const todayTasks = useMemo(() => selectTodayPlanTasks(records.filter((record) => record.module === "plans") as PlanMemo[], selectedDate), [records, selectedDate]);

  async function toggleTodayTask(item: TodayPlanTask) {
    const plan = records.find((record) => record.id === item.planId) as PlanMemo | undefined;
    if (!plan) return;
    await repository.save({
      ...plan,
      extra: { ...plan.extra, tasks: plan.extra.tasks.map((task) => (task.id === item.task.id ? { ...task, done: !task.done } : task)) },
    });
    const refreshed = await Promise.all(modules.map((module) => repository.list(module.key)));
    const all = refreshed.flat();
    setRecords(all);
    setCounts({ diary: refreshed[0].length, footprints: refreshed[1].length, plans: refreshed[2].filter((record) => record.status === "进行中").length });
  }

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
      <View style={styles.todayHeading}>
        <Text style={styles.sectionTitle}>今天</Text>
        <View style={styles.dateSwitcher}>
          <Pressable accessibilityLabel="前一天" onPress={() => setSelectedDate((value) => changeDate(value, -1))}><Text style={styles.dateButton}>←</Text></Pressable>
          <Pressable onPress={() => setSelectedDate(today())}><Text style={styles.selectedDate}>{selectedDate === today() ? "今天" : selectedDate}</Text></Pressable>
          <Pressable accessibilityLabel="后一天" onPress={() => setSelectedDate((value) => changeDate(value, 1))}><Text style={styles.dateButton}>→</Text></Pressable>
        </View>
      </View>
      <Panel>
        <Text style={styles.todayDate}>{selectedDate}</Text>
        <Text style={styles.todayLabel}>计划</Text>
        {todayTasks.length ? todayTasks.map((item) => <Pressable key={`${item.planId}-${item.task.id}`} onPress={() => void toggleTodayTask(item)} style={styles.todayTaskRow}><Text style={styles.todayTask}>○ {item.task.title || "未命名任务"}</Text><Text style={styles.todayMeta}>{item.planTitle}</Text></Pressable>) : <Text style={styles.empty}>当天没有待完成的计划任务。</Text>}
        <Text style={styles.todayLabel}>足迹</Text>
        {daily.footprints.length ? daily.footprints.map((record) => <Text key={record.id} style={styles.todayRow}>📍 {record.title}</Text>) : <Text style={styles.empty}>当天没有足迹记录。</Text>}
        <Text style={styles.todayLabel}>日记</Text>
        {daily.diaries.length ? daily.diaries.map((record) => <Text key={record.id} style={styles.todayRow}>{record.title || "无标题日记"}</Text>) : <Text style={styles.empty}>当天没有日记。</Text>}
      </Panel>
      <Text style={styles.sectionTitle}>最近更新</Text>
      <Panel>
        {recent.length ? (
          recent.map((record) => (
            <RecordRow
              key={record.id}
              meta={record.module === "diary" ? "日记" : record.module === "footprints" ? "足迹" : record.status}
              onPress={() =>
                router.push(record.module === "diary" ? "/diary" : record.module === "footprints" ? "/footprints" : "/plans")
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
  todayHeading: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  dateSwitcher: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  dateButton: { color: colors.accent, fontSize: 22, fontWeight: "700" },
  selectedDate: { color: colors.ink, fontWeight: "700" },
  todayDate: { color: colors.muted, fontSize: 13 },
  todayLabel: { color: colors.ink, fontSize: 16, fontWeight: "700", marginTop: spacing.xs },
  todayRow: { color: colors.ink, lineHeight: 22 },
  todayTaskRow: { gap: 2 },
  todayTask: { color: colors.ink, fontWeight: "600" },
  todayMeta: { color: colors.muted, fontSize: 12 },
});
