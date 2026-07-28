import { useEffect, useMemo, useRef, useState } from "react";
import { Download, Plus, Save, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { ImageManager } from "../components/records/ImageManager";
import {
  EntryImage,
  RecordItem,
  classifyEntryImages,
  exportAllEntries,
  exportAllEntriesTxt,
  listRecords,
  saveRecord,
  updateEntryImages,
  uploadEntryImages,
} from "../lib/api";
import { SaveCoordinator, shouldApplySaveResult, shouldPersistDiary } from "../lib/saveCoordinator";

function today() {
  return new Date().toISOString().slice(0, 10);
}

function newDiary(): RecordItem {
  return { id: "", title: "", subtitle: "新建草稿", body: "", date: today(), updated_at: "", extra: { images: [] } };
}

function weekdayText(value: string) {
  if (!value) return "";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return "";
  return ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"][date.getDay()];
}

function formatDate(value: string) {
  return value ? `${value} ${weekdayText(value)}` : "";
}

function sortDiaryRecords(items: RecordItem[]) {
  return [...items].sort((a, b) => {
    const dateOrder = String(b.date || "").localeCompare(String(a.date || ""));
    if (dateOrder !== 0) return dateOrder;
    return String(b.updated_at || "").localeCompare(String(a.updated_at || ""));
  });
}

function imagesOf(record: RecordItem | null): EntryImage[] {
  const raw = Array.isArray(record?.extra?.images) ? record?.extra?.images : [];
  return raw
    .map((item) => {
      if (typeof item === "string") {
        return { file_name: item, label: "", url: `/api/modules/entries/${record?.id}/images/${encodeURIComponent(item)}` };
      }
      if (typeof item === "object" && item) {
        const value = item as Record<string, unknown>;
        const fileName = String(value.file_name || value.name || "");
        return {
          file_name: fileName,
          label: String(value.label || ""),
          url: `/api/modules/entries/${record?.id}/images/${encodeURIComponent(fileName)}`,
        };
      }
      return null;
    })
    .filter((image): image is EntryImage => Boolean(image?.file_name));
}

async function filesToPayload(files: File[]) {
  return Promise.all(
    files.map(
      (file) =>
        new Promise<{ name: string; data: string }>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve({ name: file.name, data: String(reader.result || "") });
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(file);
        }),
    ),
  );
}

export function Diary() {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取日记");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [classifyOpen, setClassifyOpen] = useState(false);
  const selectedRef = useRef<RecordItem | null>(null);
  const dirtyRef = useRef(false);
  const editRevisionRef = useRef(0);
  const autoSaveTimerRef = useRef<number | null>(null);
  const switchingRef = useRef(false);
  const draftEntryIdRef = useRef("");
  const saveCoordinatorRef = useRef<SaveCoordinator | null>(null);
  if (!saveCoordinatorRef.current) {
    saveCoordinatorRef.current = new SaveCoordinator(setSaving);
  }
  selectedRef.current = selected;

  const images = useMemo(() => imagesOf(selected), [selected]);
  const wordCount = selected?.body?.length ?? 0;

  async function load(keyword = "") {
    const data = sortDiaryRecords(await listRecords("entries", keyword));
    setRecords(data);
    setSelected((current) => {
      const next = current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null;
      selectedRef.current = next;
      return next;
    });
    dirtyRef.current = false;
    setDirty(false);
    setMessage(`已读取 ${data.length} 篇日记`);
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("new")) {
      listRecords("entries")
        .then((data) => {
          setRecords(sortDiaryRecords(data));
          const draft = newDiary();
          selectedRef.current = draft;
          setSelected(draft);
          dirtyRef.current = false;
          setDirty(false);
          setMessage("已创建日记草稿");
        })
        .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
      return;
    }
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  function patch(patchValue: Partial<RecordItem>) {
    const current = selectedRef.current;
    if (!current) return;
    const next = { ...current, ...patchValue };
    selectedRef.current = next;
    editRevisionRef.current += 1;
    dirtyRef.current = true;
    setSelected(next);
    setDirty(true);
  }

  function clearAutoSaveTimer() {
    if (autoSaveTimerRef.current !== null) {
      window.clearTimeout(autoSaveTimerRef.current);
      autoSaveTimerRef.current = null;
    }
  }

  function copyRecord(record: RecordItem): RecordItem {
    const images = Array.isArray(record.extra?.images)
      ? record.extra.images.map((image) => (typeof image === "object" && image ? { ...(image as Record<string, unknown>) } : image))
      : undefined;
    return {
      ...record,
      extra: record.extra ? { ...record.extra, ...(images ? { images } : {}) } : record.extra,
    };
  }

  function updateRecordList(record: RecordItem) {
    setRecords((items) => {
      const index = items.findIndex((item) => item.id === record.id);
      const next = index < 0 ? [record, ...items.filter((item) => item.id)] : items.map((item) => (item.id === record.id ? { ...item, ...record } : item));
      return sortDiaryRecords(next);
    });
  }

  async function saveCurrent(reason = "已保存", force = false, rejectOnError = false) {
    const current = selectedRef.current;
    if (!current || !shouldPersistDiary(current)) return current;
    if (!force && !dirtyRef.current) return current;
    const snapshot = copyRecord(current);
    const savingRecordId = snapshot.id;
    const savingRevision = editRevisionRef.current;
    const task = saveCoordinatorRef.current!.enqueue(async () => {
      const payload = snapshot.id || !draftEntryIdRef.current ? snapshot : { ...snapshot, id: draftEntryIdRef.current };
      const saved = await saveRecord("entries", payload);
      if (!snapshot.id) draftEntryIdRef.current = saved.id;
      updateRecordList(saved);
      const active = selectedRef.current;
      if (active && shouldApplySaveResult(active.id, editRevisionRef.current, savingRecordId, savingRevision)) {
        selectedRef.current = saved;
        dirtyRef.current = false;
        setSelected(saved);
        setDirty(false);
        setMessage(reason);
      } else if (!snapshot.id && active && !active.id) {
        const attached = { ...active, id: saved.id, updated_at: saved.updated_at };
        selectedRef.current = attached;
        setSelected(attached);
      }
      return saved;
    });
    if (rejectOnError) return task;
    return task.catch((error) => {
      const active = selectedRef.current;
      if (active && shouldApplySaveResult(active.id, editRevisionRef.current, savingRecordId, savingRevision)) {
        setMessage(error instanceof Error ? error.message : "保存失败");
      }
      return snapshot;
    });
  }

  async function selectRecordSafely(record: RecordItem) {
    if (switchingRef.current || selectedRef.current?.id === record.id) return;
    switchingRef.current = true;
    clearAutoSaveTimer();
    try {
      await saveCurrent("已自动保存", true, true);
    } catch {
      return;
    } finally {
      switchingRef.current = false;
    }
    editRevisionRef.current += 1;
    dirtyRef.current = false;
    setDirty(false);
    selectedRef.current = record;
    setSelected(record);
  }

  async function createNewDiarySafely() {
    if (switchingRef.current) return;
    switchingRef.current = true;
    clearAutoSaveTimer();
    try {
      await saveCurrent("已自动保存", true, true);
    } catch {
      return;
    } finally {
      switchingRef.current = false;
    }
    const draft = newDiary();
    draftEntryIdRef.current = "";
    editRevisionRef.current += 1;
    dirtyRef.current = false;
    selectedRef.current = draft;
    setSelected(draft);
    setDirty(false);
    setMessage("已创建日记草稿");
  }

  useEffect(() => {
    clearAutoSaveTimer();
    if (!selected || !dirty) return;
    autoSaveTimerRef.current = window.setTimeout(() => {
      autoSaveTimerRef.current = null;
      void saveCurrent();
    }, 2800);
    return clearAutoSaveTimer;
  }, [selected?.id, selected?.title, selected?.body, selected?.date, dirty]);

  useEffect(() => {
    const protectUnsavedChanges = (event: BeforeUnloadEvent) => {
      if (!dirtyRef.current && !saveCoordinatorRef.current?.hasPendingSaves) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", protectUnsavedChanges);
    return () => window.removeEventListener("beforeunload", protectUnsavedChanges);
  }, []);

  async function uploadImages(files: File[]) {
    let target = selectedRef.current;
    if (!target?.id) target = await saveCurrent("已创建日记", true, true);
    if (!target?.id) return;
    const targetId = target.id;
    const saved = await saveCoordinatorRef.current!.enqueue(async () => uploadEntryImages(targetId, await filesToPayload(files)));
    if (selectedRef.current?.id === targetId) {
      const next = { ...selectedRef.current, extra: saved.extra, updated_at: saved.updated_at };
      setSelected(next);
      selectedRef.current = next;
    }
    updateRecordList(saved);
    setMessage(`已插入 ${files.length} 张图片`);
  }

  async function commitImages(nextImages: EntryImage[]) {
    const current = selectedRef.current;
    if (!current?.id) return;
    const optimistic = { ...current, extra: { ...(current.extra ?? {}), images: nextImages } };
    selectedRef.current = optimistic;
    setSelected(optimistic);
    updateRecordList(optimistic);
    try {
      const imageSnapshot = nextImages.map((image) => ({ file_name: image.file_name, label: image.label || "" }));
      const saved = await saveCoordinatorRef.current!.enqueue(() => updateEntryImages(current.id, imageSnapshot));
      const active = selectedRef.current;
      if (active?.id === current.id) {
        const next = { ...active, extra: saved.extra, updated_at: saved.updated_at };
        selectedRef.current = next;
        setSelected(next);
      }
      updateRecordList(saved);
      setMessage("图片已保存");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "图片保存失败");
    }
  }

  async function exportAll() {
    try {
      const result = await exportAllEntries();
      window.alert(`已全部导出 ${result.count ?? ""} 篇日记\n\n目录：${result.output_dir}\nWord：${result.docx_path}\nPDF：${result.pdf_path}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "导出失败");
    }
  }

  async function exportTxt() {
    try {
      const result = await exportAllEntriesTxt();
      window.alert(`已全部导出 ${result.count ?? ""} 篇日记为 TXT\n\n目录：${result.output_dir}\nTXT：${result.txt_path}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "导出 TXT 失败");
    }
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">日记</h2>
            <Button size="sm" onClick={createNewDiarySafely}>
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索日记..."
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && load(query)}
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {records.map((record) => (
            <button
              key={record.id}
              onClick={() => selectRecordSafely(record)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected?.id === record.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              <p className="text-xs opacity-80 mb-1">{formatDate(record.date)}</p>
              <p className="font-medium truncate">{record.title || "未命名日记"}</p>
              <p className="text-sm opacity-80 truncate mt-1">{record.body || record.subtitle}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {selected ? (
          <>
            <div className="border-b p-6 space-y-4">
              <div className="flex items-center justify-between gap-4">
                <Input
                  placeholder="日记标题"
                  className="text-xl font-semibold border-0 px-0 focus-visible:ring-0"
                  value={selected.title}
                  onChange={(event) => patch({ title: event.target.value })}
                />
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => saveCurrent("已手动保存", true)} disabled={saving}>
                    <Save className="size-4" />
                    保存
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <Input className="w-40" value={selected.date || ""} onChange={(event) => patch({ date: event.target.value })} />
                <span className="text-muted-foreground">{weekdayText(selected.date)}</span>
                <span className="text-muted-foreground">字数: {wordCount}</span>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <Textarea
                autoParagraphIndent
                placeholder="开始写日记..."
                className="min-h-[420px] border-0 resize-none text-base leading-relaxed focus-visible:ring-0"
                value={selected.body || ""}
                onChange={(event) => patch({ body: event.target.value })}
              />
            </div>
            <ImageManager
              images={images}
              onUpload={uploadImages}
              onChange={(nextImages) => {
                const next = { ...selected, extra: { ...(selected.extra ?? {}), images: nextImages } };
                selectedRef.current = next;
                setSelected(next);
              }}
              onCommit={commitImages}
              extraAction={
                <Button variant="outline" size="sm" disabled={!selected.id || images.length === 0} onClick={() => setClassifyOpen(true)}>
                  归类
                </Button>
              }
            />
            <div className="p-4 border-t flex gap-3">
              <Button variant="outline" size="sm" onClick={exportAll}>
                <Download className="size-4" />
                全部导出 Word / PDF
              </Button>
              <Button variant="outline" size="sm" onClick={exportTxt}>
                <Download className="size-4" />
                全部导出 TXT
              </Button>
            </div>
            {classifyOpen && selected.id && (
              <ClassifyDialog entry={selected} images={images} onClose={() => setClassifyOpen(false)} onMessage={setMessage} />
            )}
          </>
        ) : (
          <div className="flex-1 grid place-content-center text-muted-foreground">选择一篇日记开始编辑</div>
        )}
      </div>
    </div>
  );
}

function ClassifyDialog({
  entry,
  images,
  onClose,
  onMessage,
}: {
  entry: RecordItem;
  images: EntryImage[];
  onClose: () => void;
  onMessage: (message: string) => void;
}) {
  const [footprints, setFootprints] = useState<RecordItem[]>([]);
  const [footprintId, setFootprintId] = useState("");
  const [date, setDate] = useState(entry.date || today());
  const [selectedNames, setSelectedNames] = useState<string[]>(images.map((image) => image.file_name));

  useEffect(() => {
    listRecords("footprints").then((items) => {
      setFootprints(items);
      setFootprintId(items[0]?.id || "");
    });
  }, []);

  async function submit() {
    if (!footprintId || selectedNames.length === 0) return;
    const result = await classifyEntryImages(entry.id, { footprint_id: footprintId, date, images: selectedNames });
    onMessage(`已归类 ${result.copied} 张图片到足迹`);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/35 flex items-center justify-center">
      <div className="w-[680px] rounded-lg bg-background border shadow-xl p-6 space-y-5">
        <div>
          <h3 className="text-lg font-semibold">图片归类到足迹</h3>
          <p className="text-sm text-muted-foreground mt-1">复制当前日记图片到指定足迹的日期分组。</p>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <label className="space-y-2">
            <span className="text-sm text-muted-foreground">足迹</span>
            <div className="max-h-28 overflow-y-auto rounded-md border bg-background p-1">
              {footprints.length === 0 ? (
                <div className="px-3 py-2 text-sm text-muted-foreground">暂无足迹</div>
              ) : (
                footprints.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={`w-full rounded px-3 py-2 text-left text-sm transition-colors ${
                      footprintId === item.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
                    }`}
                    onClick={() => setFootprintId(item.id)}
                  >
                    {item.title || "未命名足迹"}
                  </button>
                ))
              )}
            </div>
          </label>
          <label className="space-y-2">
            <span className="text-sm text-muted-foreground">日期</span>
            <Input value={date} onChange={(event) => setDate(event.target.value)} />
          </label>
        </div>
        <div className="grid grid-cols-5 gap-3">
          {images.map((image) => (
            <label key={image.file_name} className="space-y-2">
              <img src={image.url} className="aspect-square rounded-md object-cover border" />
              <span className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={selectedNames.includes(image.file_name)}
                  onChange={(event) =>
                    setSelectedNames((names) =>
                      event.target.checked ? [...names, image.file_name] : names.filter((name) => name !== image.file_name),
                    )
                  }
                />
                {image.label || image.file_name}
              </span>
            </label>
          ))}
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={submit}>归类</Button>
        </div>
      </div>
    </div>
  );
}
