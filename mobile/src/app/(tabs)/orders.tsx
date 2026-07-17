import { useMemo, useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { ButtonRow, Field, Panel, PrimaryButton, SecondaryButton } from "@/components/Controls";
import { EmptyState } from "@/components/EmptyState";
import { RecordRow } from "@/components/RecordRow";
import { Screen } from "@/components/Screen";
import { StatusBanner } from "@/components/StatusBanner";
import type { ArchiveRecord, NewRecord, OrderMemo } from "@/domain/models";
import { emptyOrder, ORDER_STATUSES } from "@/domain/models";
import { sortOrderMemos } from "@/domain/orderSort";
import { useModuleRecords } from "@/hooks/useModuleRecords";
import { colors, spacing } from "@/theme";

function editable(record?: ArchiveRecord): NewRecord {
  return record ? { ...record } : emptyOrder();
}

const FIELD_NAMES: [string, string][] = [
  ["customer", "客户"],
  ["intermediary", "中间人"],
  ["executor", "执行人"],
  ["orderDate", "接单日期"],
  ["deadline", "截止日期"],
  ["durationDays", "周期（天）"],
  ["price", "总价"],
  ["deposit", "定金"],
  ["finalPayment", "尾款"],
  ["deliverables", "交付内容"],
];

export default function OrdersScreen() {
  const { repository, records, loading, refresh } = useModuleRecords("orders");
  const [draft, setDraft] = useState<NewRecord | null>(null);
  const [message, setMessage] = useState("");
  const sorted = useMemo(() => sortOrderMemos(records as OrderMemo[]), [records]);

  async function save() {
    if (!draft) return;
    const saved = await repository.save(draft);
    setDraft(editable(saved));
    setMessage("接单记录已保存");
    await refresh();
  }

  function remove() {
    if (!draft?.id) return;
    Alert.alert("删除接单记录", "记录会被软删除。", [
      { text: "取消", style: "cancel" },
      {
        text: "删除",
        style: "destructive",
        onPress: async () => {
          await repository.softDelete(draft.id!);
          setDraft(null);
          await refresh();
        },
      },
    ]);
  }

  if (draft) {
    return (
      <Screen
        action={<SecondaryButton label="返回列表" onPress={() => setDraft(null)} />}
        subtitle="状态标签会同步影响列表优先级"
        title={draft.id ? "编辑接单" : "新建接单"}
      >
        <StatusBanner text={message} />
        <Panel>
          <Field label="项目名称" onChangeText={(title) => setDraft({ ...draft, title })} value={draft.title} />
          <Text style={styles.label}>当前状态</Text>
          <View style={styles.statuses}>
            {ORDER_STATUSES.map((status) => (
              <Pressable
                key={status}
                onPress={() => setDraft({ ...draft, status })}
                style={[styles.status, draft.status === status && styles.statusActive]}
              >
                <Text style={[styles.statusText, draft.status === status && styles.statusTextActive]}>{status}</Text>
              </Pressable>
            ))}
          </View>
          <Field label="记录日期" onChangeText={(date) => setDraft({ ...draft, date })} value={draft.date} />
          {FIELD_NAMES.map(([key, label]) => (
            <Field
              key={key}
              label={label}
              multiline={key === "deliverables"}
              onChangeText={(value) => setDraft({ ...draft, extra: { ...draft.extra, [key]: value } })}
              value={String(draft.extra[key] || "")}
            />
          ))}
          <Field
            label="备注"
            multiline
            onChangeText={(body) => setDraft({ ...draft, body })}
            value={draft.body}
          />
          <ButtonRow>
            <PrimaryButton label="保存" onPress={save} />
            {draft.id ? <SecondaryButton danger label="删除" onPress={remove} /> : null}
          </ButtonRow>
        </Panel>
      </Screen>
    );
  }

  return (
    <Screen
      action={<PrimaryButton label="新建" onPress={() => setDraft(emptyOrder())} />}
      subtitle="已接单未完成优先，其次是已验收未结款"
      title="接单备忘"
    >
      <Panel>
        {!sorted.length ? (
          <EmptyState text={loading ? "正在读取……" : "还没有接单记录"} />
        ) : (
          sorted.map((record) => (
            <RecordRow
              key={record.id}
              meta={record.status}
              onPress={() => setDraft(editable(record))}
              record={record}
            />
          ))
        )}
      </Panel>
    </Screen>
  );
}

const styles = StyleSheet.create({
  label: { color: colors.muted, fontSize: 13, fontWeight: "600" },
  statuses: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  status: {
    minHeight: 38,
    justifyContent: "center",
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 18,
    paddingHorizontal: 14,
    backgroundColor: colors.surface,
  },
  statusActive: { borderColor: colors.accent, backgroundColor: colors.accentSoft },
  statusText: { color: colors.muted, fontWeight: "600" },
  statusTextActive: { color: colors.accent },
});
