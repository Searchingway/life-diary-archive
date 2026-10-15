import { useEffect, useMemo, useRef, useState } from "react";
import { useBlocker } from "react-router";
import { calendarDate } from "../lib/calendarDate";
import { Download, Plus, Save, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { ImageManager } from "../components/records/ImageManager";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
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
  return calendarDate();
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
  const [loading, setLoading] = useState(true);
  const [pendingTransition, setPendingTransition] = useState<(() => Promise<void> | void) | null>(null);
  const [transitionBusy, setTransitionBusy] = useState(false);
  const [transitionError, setTransitionError] = useState("");
  const selectedRef = useRef<RecordItem | null>(null);
  const dirtyRef = useRef(false);
  const editRevisionRef = useRef(0);
  const autoSaveTimerRef = useRef<number | null>(null);
  const switchingRef = useRef(false);
  const draftEntryIdRef = useRef("");
  const loadRevisionRef = useRef(0);
  const saveCoordinatorRef = useRef<SaveCoordinator | null>(null);
  if (!saveCoordinatorRef.current) {
    saveCoordinatorRef.current = new SaveCoordinator(setSaving);
  }
  selectedRef.current = selected;
  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    (dirtyRef.current || Boolean(saveCoordinatorRef.current?.hasPendingSaves)) &&
    (currentLocation.pathname !== nextLocation.pathname || currentLocation.search !== nextLocation.search),
  );
  const transitionOpen = Boolean(pendingTransition) || blocker.state === "blocked";

  const images = useMemo(() => imagesOf(selected), [selected]);
  const wordCount = selected?.body?.length ?? 0;

  async function load(keyword = "") {
    const revision = ++loadRevisionRef.current;
    setLoading(true);
    try {
      const data = sortDiaryRecords(await listRecords("entries", keyword));
      if (revision !== loadRevisionRef.current) return;
      setRecords(data);
      if (!dirtyRef.current && !saveCoordinatorRef.current?.hasPendingSaves) {
        const current = selectedRef.current;
        const requestedId = new URLSearchParams(window.location.search).get("id");
        const next = data.find((item) => item.id === (current?.id || requestedId)) ?? data[0] ?? null;
        selectedRef.current = next;
        setSelected(next);
        draftEntryIdRef.current = "";
      }
      setMessage(data.length ? `已读取 ${data.length} 篇日记` : keyword ? "没有匹配的日记，试试其他关键词" : "还没有日记，点击新建开始记录");
    } catch (error) {
      if (revision === loadRevisionRef.current) setMessage(error instanceof Error ? error.message : "读取失败，请重试");
    } finally {
      if (revision === loadRevisionRef.current) setLoading(false);
    }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("new")) {
      let active = true;
      listRecords("entries")
        .then((data) => {
          if (!active) return;
          setRecords(sortDiaryRecords(data));
          const draft = newDiary();
          selectedRef.current = draft;
          setSelected(draft);
          dirtyRef.current = false;
          setDirty(false);
          setMessage("已创建日记草稿");
        })
        .catch((error) => { if (active) setMessage(error instanceof Error ? error.message : "读取失败"); })
        .finally(() => { if (active) setLoading(false); });
      return () => { active = false; };
    }
    void load("");
    return () => { loadRevisionRef.current += 1; };
  }, []);

  function patch(patchValue: Partial<RecordItem>) {
    if (switchingRef.current) return;
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

  function requestTransition(action: () => Promise<void> | void) {
    if (switchingRef.current || transitionOpen) return;
    clearAutoSaveTimer();
    if (dirtyRef.current || saveCoordinatorRef.current?.hasPendingSaves) {
      setTransitionError("");
      setPendingTransition(() => action);
    } else {
      void action();
    }
  }

  function cancelTransition() {
    if (switchingRef.current) return;
    setPendingTransition(null);
    setTransitionError("");
    if (blocker.state === "blocked") blocker.reset();
  }

  async function completeTransition(save: boolean) {
    if (switchingRef.current) return;
    switchingRef.current = true;
    setTransitionBusy(true);
    clearAutoSaveTimer();
    try {
      if (save) await saveCurrent("已保存", true, true);
      else await saveCoordinatorRef.current!.waitForIdle();
      editRevisionRef.current += 1;
      dirtyRef.current = false;
      setDirty(false);
      setPendingTransition(null);
      setTransitionError("");
      if (blocker.state === "blocked") blocker.proceed();
      else await pendingTransition?.();
    } catch (error) {
      const detail = error instanceof Error ? error.message : "保存失败";
      setTransitionError(`${detail}。草稿仍保留，请重试或取消切换。`);
      setMessage("保存失败，草稿仍保留");
    } finally {
      switchingRef.current = false;
      setTransitionBusy(false);
    }
  }

  function selectRecordSafely(record: RecordItem) {
    if (selectedRef.current?.id === record.id) return;
    requestTransition(() => selectRecord(record));
  }

  function selectRecord(record: RecordItem) {
    editRevisionRef.current += 1;
    dirtyRef.current = false;
    setDirty(false);
    selectedRef.current = record;
    draftEntryIdRef.current = "";
    setSelected(record);
    setMessage("已切换日记");
  }

  function createNewDiarySafely() {
    requestTransition(createNewDiary);
  }

  function createNewDiary() {
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
    if (!selected || !dirty || transitionOpen) return;
    autoSaveTimerRef.current = window.setTimeout(() => {
      autoSaveTimerRef.current = null;
      void saveCurrent();
    }, 2800);
    return clearAutoSaveTimer;
  }, [selected?.id, selected?.title, selected?.body, selected?.date, dirty, transitionOpen]);

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
            <Button size="sm" onClick={createNewDiarySafely} disabled={loading || transitionBusy}>
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
              aria-label="搜索日记"
              disabled={transitionBusy}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.nativeEvent.isComposing) {
                  event.preventDefault();
                  requestTransition(() => load(query));
                }
              }}
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {!records.length && <p className="p-4 text-sm text-muted-foreground">{loading ? "正在读取日记…" : message}</p>}
          {records.map((record) => (
            <button
              key={record.id}
              onClick={() => selectRecordSafely(record)}
              disabled={transitionBusy}
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
                  disabled={transitionBusy}
                  onChange={(event) => patch({ title: event.target.value })}
                />
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => saveCurrent("已手动保存", true)} disabled={saving || transitionBusy}>
                    <Save className="size-4" />
                    保存
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <Input type="date" aria-label="日记日期" className="w-40" disabled={transitionBusy} value={selected.date || ""} onChange={(event) => patch({ date: event.target.value })} />
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
                disabled={transitionBusy}
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
      <div className="fixed bottom-0 right-0 max-w-[calc(100%-1rem)] rounded-tl-md border bg-background px-4 py-1.5 text-xs text-muted-foreground" role="status" aria-live="polite">
        {saving ? "正在保存…" : dirty ? `未保存 · ${message}` : message}
      </div>
      <Dialog open={transitionOpen} onOpenChange={(open) => { if (!open) cancelTransition(); }}>
        <DialogContent onEscapeKeyDown={(event) => { if (transitionBusy) event.preventDefault(); }} onPointerDownOutside={(event) => { if (transitionBusy) event.preventDefault(); }}>
          <DialogHeader>
            <DialogTitle>保存当前日记？</DialogTitle>
            <DialogDescription>当前日记有尚未保存的修改。选择保存后继续、放弃修改，或返回继续写作。</DialogDescription>
          </DialogHeader>
          {transitionError && <p role="alert" className="text-sm text-destructive">{transitionError}</p>}
          <DialogFooter>
            <Button variant="outline" disabled={transitionBusy} onClick={cancelTransition}>取消切换</Button>
            <Button variant="outline" disabled={transitionBusy} onClick={() => completeTransition(false)}>放弃修改并继续</Button>
            <Button disabled={transitionBusy} onClick={() => completeTransition(true)}>{transitionBusy ? "处理中…" : "保存并继续"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
