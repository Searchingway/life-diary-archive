import { useMemo, useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { ButtonRow, Field, Panel, PrimaryButton, SecondaryButton } from "@/components/Controls";
import { EmptyState } from "@/components/EmptyState";
import { Screen } from "@/components/Screen";
import { StatusBanner } from "@/components/StatusBanner";
import type { ArchiveRecord, NewRecord } from "@/domain/models";
import {
  emptyPlan,
  PLAN_PRIORITIES,
  PLAN_STATUSES,
  planProgress,
  sortPlans,
  type PlanExtra,
  type PlanMemo,
  type PlanPriority,
  type PlanStatus,
  type PlanTask,
} from "@/domain/plans";
import { today } from "@/domain/models";
import { useModuleRecords } from "@/hooks/useModuleRecords";
import { colors, spacing } from "@/theme";

function editable(record?: ArchiveRecord): NewRecord {
  return record ? { ...record } : emptyPlan();
}

function extraOf(record: NewRecord): PlanExtra {
  const source = record.extra;
  const rawTasks = Array.isArray(source.tasks) ? (source.tasks as Array<Record<string, unknown>>) : [];
  return {
    ...source,
    schema_version: 2,
    goal: String(record.extra.goal || ""),
    start_date: String(record.extra.start_date || record.extra.startDate || record.date || today()),
    due_date: String(record.extra.due_date || record.extra.deadline || ""),
    priority: (PLAN_PRIORITIES.includes(record.extra.priority as PlanPriority) ? record.extra.priority : "中") as PlanPriority,
    notes: String(record.extra.notes ?? record.body ?? ""),
    tags: Array.isArray(record.extra.tags) ? record.extra.tags.map(String) : [],
    plan_type: record.extra.plan_type === "subtract" ? "subtract" : "add",
    tasks: rawTasks.map((task, index) => ({ id: String(task.id || `task-${index + 1}`), title: String(task.title || ""), scheduled_date: String(task.scheduled_date || task.scheduledDate || task.date || ""), done: Boolean(task.done), note: String(task.note || "") })),
  };
}

function newTask(): PlanTask {
  return { id: `task-${Date.now()}-${Math.random().toString(16).slice(2)}`, title: "", scheduled_date: "", done: false, note: "" };
}

export default function PlansScreen() {
  const { repository, records, loading, refresh } = useModuleRecords("plans");
  const [draft, setDraft] = useState<NewRecord | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState(false);
  const plans = useMemo(() => sortPlans(records as PlanMemo[]), [records]);

  async function save() {
    if (!draft) return;
    setError(false);
    setMessage("");
    try {
      const saved = await repository.save(draft);
      setDraft(editable(saved));
      setMessage("计划已保存到本机");
      await refresh(query);
    } catch (reason) {
      setError(true);
      setMessage(reason instanceof Error ? reason.message : String(reason));
    }
  }

  function remove() {
    if (!draft?.id) return;
    Alert.alert("删除计划？", "计划将被移入软删除状态，不会立即物理清除。", [
      { text: "取消", style: "cancel" },
      {
        text: "删除",
        style: "destructive",
        onPress: async () => {
          try {
            await repository.softDelete(draft.id!);
            setDraft(null);
            await refresh(query);
          } catch (reason) {
            setError(true);
            setMessage(reason instanceof Error ? reason.message : String(reason));
          }
        },
      },
    ]);
  }

  function updateExtra(next: PlanExtra) {
    if (draft) setDraft({ ...draft, body: next.notes, type: next.plan_type, extra: next });
  }

  function toggleTask(task: PlanTask) {
    if (!draft) return;
    const extra = extraOf(draft);
    const tasks = extra.tasks.map((item) => (item.id === task.id ? { ...item, done: !item.done } : item));
    updateExtra({ ...extra, tasks });
    if (!task.done && tasks.length > 0 && tasks.every((item) => item.done) && draft.status !== "已完成") {
      Alert.alert("所有任务已经完成", "是否将计划标记为“已完成”？", [
        { text: "暂不修改", style: "cancel" },
        { text: "标记为已完成", onPress: () => setDraft((current) => (current ? { ...current, status: "已完成" } : current)) },
      ]);
    }
  }

  if (draft) {
    const extra = extraOf(draft);
    const progress = planProgress(extra.tasks);
    return (
      <Screen action={<SecondaryButton label="返回列表" onPress={() => setDraft(null)} />} subtitle="保存失败时会保留当前填写内容" title={draft.id ? "编辑计划" : "新建计划"}>
        <StatusBanner error={error} text={message} />
        <Panel>
          <Field label="计划名称" onChangeText={(title) => setDraft({ ...draft, title })} value={draft.title} />
          <Field label="目标" autoParagraphIndent multiline onChangeText={(goal) => updateExtra({ ...extra, goal })} value={extra.goal} />
          <Field label="开始日期" onChangeText={(start_date) => updateExtra({ ...extra, start_date })} value={extra.start_date} />
          <Field label="截止日期" onChangeText={(due_date) => updateExtra({ ...extra, due_date })} value={extra.due_date} />
          <Text style={styles.label}>优先级</Text>
          <View style={styles.options}>
            {PLAN_PRIORITIES.map((priority) => (
              <Pressable key={priority} onPress={() => updateExtra({ ...extra, priority })} style={[styles.option, extra.priority === priority && styles.optionActive]}>
                <Text style={[styles.optionText, extra.priority === priority && styles.optionTextActive]}>{priority}</Text>
              </Pressable>
            ))}
          </View>
          <Text style={styles.label}>状态</Text>
          <View style={styles.options}>
            {PLAN_STATUSES.map((status) => (
              <Pressable key={status} onPress={() => setDraft({ ...draft, status })} style={[styles.option, draft.status === status && styles.optionActive]}>
                <Text style={[styles.optionText, draft.status === status && styles.optionTextActive]}>{status}</Text>
              </Pressable>
            ))}
          </View>
          <Field label="备注" autoParagraphIndent multiline onChangeText={(notes) => updateExtra({ ...extra, notes })} value={extra.notes} />
        </Panel>
        <View style={styles.sectionHeading}>
          <View>
            <Text style={styles.sectionTitle}>任务 Checklist</Text>
            <Text style={styles.progress}>{progress}% · {extra.tasks.filter((task) => task.done).length} / {extra.tasks.length} 个任务</Text>
          </View>
          <SecondaryButton label="添加任务" onPress={() => updateExtra({ ...extra, tasks: [...extra.tasks, newTask()] })} />
        </View>
        {extra.tasks.map((task) => (
          <Panel key={task.id}>
            <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: task.done }} onPress={() => toggleTask(task)} style={styles.taskCheck}>
              <Text style={[styles.checkMark, task.done && styles.checkMarkDone]}>{task.done ? "✓ 已完成" : "○ 未完成"}</Text>
            </Pressable>
            <Field label="任务名称" onChangeText={(title) => updateExtra({ ...extra, tasks: extra.tasks.map((item) => (item.id === task.id ? { ...item, title } : item)) })} value={task.title} />
            <Field label="任务日期（可选）" onChangeText={(scheduled_date) => updateExtra({ ...extra, tasks: extra.tasks.map((item) => (item.id === task.id ? { ...item, scheduled_date } : item)) })} value={task.scheduled_date} />
            <Field label="任务备注（可选）" autoParagraphIndent multiline onChangeText={(note) => updateExtra({ ...extra, tasks: extra.tasks.map((item) => (item.id === task.id ? { ...item, note } : item)) })} value={task.note} />
            <SecondaryButton danger label="删除任务" onPress={() => updateExtra({ ...extra, tasks: extra.tasks.filter((item) => item.id !== task.id) })} />
          </Panel>
        ))}
        <ButtonRow>
          <PrimaryButton label="保存计划" onPress={save} />
          {draft.id ? <SecondaryButton danger label="删除计划" onPress={remove} /> : null}
        </ButtonRow>
      </Screen>
    );
  }

  return (
    <Screen action={<PrimaryButton label="新建计划" onPress={() => setDraft(emptyPlan())} />} subtitle="按逾期、今日任务、状态和截止日期排序" title="计划">
      <StatusBanner error={error} text={message} />
      <Field label="搜索" onChangeText={(value) => { setQuery(value); void refresh(value); }} placeholder="标题、目标、备注、子任务或状态" value={query} />
      <Panel>
        {!plans.length ? <EmptyState text={loading ? "正在读取…" : "还没有计划，先新建一个吧。"} /> : plans.map((plan) => {
          const done = plan.extra.tasks.filter((task) => task.done).length;
          const overdueDays = plan.extra.due_date && plan.extra.due_date < today() && plan.status !== "已完成" && plan.status !== "已暂停"
            ? Math.floor((Date.parse(`${today()}T00:00:00`) - Date.parse(`${plan.extra.due_date}T00:00:00`)) / 86_400_000)
            : 0;
          return (
            <Pressable key={plan.id} onPress={() => setDraft(editable(plan))} style={styles.planRow}>
              <Text style={styles.planTitle}>{plan.title || "未命名计划"}</Text>
              <Text style={styles.planMeta}>{plan.status} · {plan.extra.priority}优先级</Text>
              <View style={styles.progressTrack}><View style={[styles.progressFill, { width: `${planProgress(plan.extra.tasks)}%` }]} /></View>
              <Text style={styles.planMeta}>{done} / {plan.extra.tasks.length} 个任务 · {planProgress(plan.extra.tasks)}%</Text>
              <Text style={[styles.planMeta, overdueDays > 0 && styles.overdue]}>{overdueDays > 0 ? `已逾期 ${overdueDays} 天` : plan.extra.due_date ? `截止：${plan.extra.due_date}` : "未设置截止日期"}</Text>
            </Pressable>
          );
        })}
      </Panel>
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: { color: colors.muted, fontSize: 13, fontWeight: "600" },
  options: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  option: { minHeight: 38, justifyContent: "center", borderWidth: 1, borderColor: colors.line, borderRadius: 18, paddingHorizontal: 14, backgroundColor: colors.surface },
  optionActive: { borderColor: colors.accent, backgroundColor: colors.accentSoft },
  optionText: { color: colors.muted, fontWeight: "600" },
  optionTextActive: { color: colors.accent },
  sectionHeading: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  sectionTitle: { color: colors.ink, fontSize: 19, fontWeight: "700" },
  progress: { color: colors.muted, fontSize: 13, marginTop: 3 },
  taskCheck: { alignSelf: "flex-start" },
  checkMark: { color: colors.muted, fontWeight: "700" },
  checkMarkDone: { color: colors.accent },
  planRow: { gap: 7, paddingVertical: spacing.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.line },
  planTitle: { color: colors.ink, fontSize: 17, fontWeight: "700" },
  planMeta: { color: colors.muted, fontSize: 13 },
  overdue: { color: colors.danger, fontWeight: "700" },
  progressTrack: { height: 7, borderRadius: 4, overflow: "hidden", backgroundColor: colors.accentSoft },
  progressFill: { height: "100%", borderRadius: 4, backgroundColor: colors.accent },
});
