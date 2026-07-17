import { useEffect, useMemo, useState } from "react";
import { Alert } from "react-native";

import { ButtonRow, Field, Panel, PrimaryButton, SecondaryButton } from "@/components/Controls";
import { EmptyState } from "@/components/EmptyState";
import { RecordRow } from "@/components/RecordRow";
import { Screen } from "@/components/Screen";
import { StatusBanner } from "@/components/StatusBanner";
import type { ArchiveRecord, ImageRef, NewRecord } from "@/domain/models";
import { emptyDiary } from "@/domain/models";
import { ImageStrip } from "@/features/images/ImageStrip";
import { useModuleRecords } from "@/hooks/useModuleRecords";

function editable(record?: ArchiveRecord): NewRecord {
  return record ? { ...record } : emptyDiary();
}

export default function DiaryScreen() {
  const { repository, records, loading, refresh } = useModuleRecords("diary");
  const [draft, setDraft] = useState<NewRecord | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const images = useMemo(() => (Array.isArray(draft?.extra.images) ? (draft?.extra.images as ImageRef[]) : []), [draft]);

  useEffect(() => {
    if (!draft || (!draft.id && !draft.title && !draft.body)) return;
    const timer = setTimeout(async () => {
      try {
        const wasNew = !draft.id;
        const saved = await repository.save(draft);
        if (wasNew) setDraft(editable(saved));
        setMessage("已自动保存");
        await refresh(query);
      } catch (reason) {
        setMessage(reason instanceof Error ? reason.message : String(reason));
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [draft, query, refresh, repository]);

  async function save() {
    if (!draft) return;
    const wasNew = !draft.id;
    const saved = await repository.save(draft);
    if (wasNew) setDraft(editable(saved));
    setMessage("已保存到本机");
    await refresh(query);
  }

  function remove() {
    if (!draft?.id) return;
    Alert.alert("移入回收状态", "记录会被软删除，不会立即清理图片。", [
      { text: "取消", style: "cancel" },
      {
        text: "删除",
        style: "destructive",
        onPress: async () => {
          await repository.softDelete(draft.id!);
          setDraft(null);
          await refresh(query);
        },
      },
    ]);
  }

  if (draft) {
    return (
      <Screen
        action={<SecondaryButton label="返回列表" onPress={() => setDraft(null)} />}
        subtitle="正文每 3 秒自动保存，也可手动保存"
        title={draft.id ? "编辑日记" : "新建日记"}
      >
        <StatusBanner text={message} />
        <Panel>
          <Field label="日期" onChangeText={(date) => setDraft({ ...draft, date })} value={draft.date} />
          <Field label="标题" onChangeText={(title) => setDraft({ ...draft, title })} value={draft.title} />
          <Field
            label="正文"
            multiline
            onChangeText={(body) => setDraft({ ...draft, body })}
            placeholder="写下今天发生的事……"
            value={draft.body}
          />
          <ImageStrip
            images={images}
            onChange={(nextImages) => setDraft({ ...draft, extra: { ...draft.extra, images: nextImages } })}
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
      action={<PrimaryButton label="新建" onPress={() => setDraft(emptyDiary())} />}
      subtitle="本地保存，按日期倒序"
      title="日记"
    >
      <Field
        label="搜索"
        onChangeText={(value) => {
          setQuery(value);
          void refresh(value);
        }}
        placeholder="搜索标题或正文"
        value={query}
      />
      <Panel>
        {!records.length ? (
          <EmptyState text={loading ? "正在读取……" : "还没有日记"} />
        ) : (
          records.map((record) => (
            <RecordRow key={record.id} onPress={() => setDraft(editable(record))} record={record} />
          ))
        )}
      </Panel>
    </Screen>
  );
}
