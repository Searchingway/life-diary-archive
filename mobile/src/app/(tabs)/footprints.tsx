import { useState } from "react";
import { Alert, StyleSheet, Text, View } from "react-native";

import { ButtonRow, Field, Panel, PrimaryButton, SecondaryButton } from "@/components/Controls";
import { EmptyState } from "@/components/EmptyState";
import { RecordRow } from "@/components/RecordRow";
import { Screen } from "@/components/Screen";
import { StatusBanner } from "@/components/StatusBanner";
import type { ArchiveRecord, FootprintVisit, NewRecord } from "@/domain/models";
import { emptyFootprint, today } from "@/domain/models";
import { ImageStrip } from "@/features/images/ImageStrip";
import { useModuleRecords } from "@/hooks/useModuleRecords";
import { colors } from "@/theme";

function editable(record?: ArchiveRecord): NewRecord {
  return record ? { ...record } : emptyFootprint();
}

function newVisit(): FootprintVisit {
  const timestamp = new Date().toISOString();
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    date: today(),
    thought: "",
    images: [],
    createdAt: timestamp,
    updatedAt: timestamp,
  };
}

export default function FootprintsScreen() {
  const { repository, records, loading, refresh } = useModuleRecords("footprints");
  const [draft, setDraft] = useState<NewRecord | null>(null);
  const [message, setMessage] = useState("");
  const visits = Array.isArray(draft?.extra.visits) ? (draft?.extra.visits as FootprintVisit[]) : [];

  function setVisits(next: FootprintVisit[]) {
    if (draft) setDraft({ ...draft, extra: { ...draft.extra, visits: next } });
  }

  async function save() {
    if (!draft) return;
    const saved = await repository.save({
      ...draft,
      date: visits.map((visit) => visit.date).sort().at(-1) || draft.date,
    });
    setDraft(editable(saved));
    setMessage("足迹已保存");
    await refresh();
  }

  function remove() {
    if (!draft?.id) return;
    Alert.alert("删除足迹", "此操作会将足迹标记为已删除。", [
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
        subtitle="一个地点可以保存多次访问记录"
        title={draft.id ? "编辑足迹" : "新建足迹"}
      >
        <StatusBanner text={message} />
        <Panel>
          <Field
            label="地点名称"
            onChangeText={(title) => setDraft({ ...draft, title })}
            placeholder="例如：东北农业大学武术馆"
            value={draft.title}
          />
          <Field
            label="地点描述"
            multiline
            onChangeText={(body) => setDraft({ ...draft, body })}
            value={draft.body}
          />
        </Panel>
        <View style={styles.sectionHeading}>
          <Text style={styles.sectionTitle}>访问记录</Text>
          <SecondaryButton label="添加访问" onPress={() => setVisits([...visits, newVisit()])} />
        </View>
        {visits.map((visit, index) => (
          <Panel key={visit.id}>
            <Field
              label={`第 ${index + 1} 次访问日期`}
              onChangeText={(date) =>
                setVisits(visits.map((item) => (item.id === visit.id ? { ...item, date, updatedAt: new Date().toISOString() } : item)))
              }
              value={visit.date}
            />
            <Field
              label="这次的想法"
              multiline
              onChangeText={(thought) =>
                setVisits(visits.map((item) => (item.id === visit.id ? { ...item, thought, updatedAt: new Date().toISOString() } : item)))
              }
              value={visit.thought}
            />
            <ImageStrip
              images={visit.images}
              onChange={(images) =>
                setVisits(visits.map((item) => (item.id === visit.id ? { ...item, images, updatedAt: new Date().toISOString() } : item)))
              }
              title="本次图片"
            />
            <SecondaryButton danger label="删除本次访问" onPress={() => setVisits(visits.filter((item) => item.id !== visit.id))} />
          </Panel>
        ))}
        <ButtonRow>
          <PrimaryButton label="保存足迹" onPress={save} />
          {draft.id ? <SecondaryButton danger label="删除足迹" onPress={remove} /> : null}
        </ButtonRow>
      </Screen>
    );
  }

  return (
    <Screen
      action={<PrimaryButton label="新建" onPress={() => setDraft(emptyFootprint())} />}
      subtitle="左侧标题统一使用地点名称"
      title="足迹"
    >
      <Panel>
        {!records.length ? (
          <EmptyState text={loading ? "正在读取……" : "还没有足迹"} />
        ) : (
          records.map((record) => {
            const count = Array.isArray(record.extra.visits) ? record.extra.visits.length : 0;
            return (
              <RecordRow
                key={record.id}
                meta={`${count} 次访问`}
                onPress={() => setDraft(editable(record))}
                record={record}
              />
            );
          })
        )}
      </Panel>
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionHeading: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  sectionTitle: { color: colors.ink, fontSize: 19, fontWeight: "700" },
});
