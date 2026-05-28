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
  listRecords,
  saveRecord,
  updateEntryImages,
  uploadEntryImages,
} from "../lib/api";

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
  const [classifyOpen, setClassifyOpen] = useState(false);
  const selectedRef = useRef<RecordItem | null>(null);
  selectedRef.current = selected;

  const images = useMemo(() => imagesOf(selected), [selected]);
  const wordCount = selected?.body?.length ?? 0;

  async function load(keyword = "") {
    const data = await listRecords("entries", keyword);
    setRecords(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
    setMessage(`已读取 ${data.length} 篇日记`);
  }

  useEffect(() => {
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  function patch(patchValue: Partial<RecordItem>) {
    setSelected((current) => (current ? { ...current, ...patchValue } : current));
  }

  function updateRecordList(record: RecordItem) {
    setRecords((items) => {
      const index = items.findIndex((item) => item.id === record.id);
      if (index < 0) return [record, ...items.filter((item) => item.id)];
      return items.map((item) => (item.id === record.id ? { ...item, ...record } : item));
    });
  }

  async function saveCurrent(reason = "已自动保存") {
    const current = selectedRef.current;
    if (!current || (!current.id && !current.title.trim() && !current.body.trim())) return current;
    setSaving(true);
    try {
      const saved = await saveRecord("entries", current);
      const next = current.id ? { ...current, updated_at: saved.updated_at } : saved;
      selectedRef.current = next;
      if (!current.id) {
        setSelected(next);
      }
      updateRecordList(next);
      setMessage(`${reason} ${new Date().toLocaleTimeString()}`);
      return next;
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存失败");
      return current;
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    if (!selected) return;
    const timer = window.setTimeout(() => {
      saveCurrent();
    }, 2000);
    return () => window.clearTimeout(timer);
  }, [selected?.id, selected?.title, selected?.body, selected?.date]);

  async function uploadImages(files: File[]) {
    let target = selectedRef.current;
    if (!target?.id) target = await saveCurrent("已创建日记");
    if (!target?.id) return;
    const saved = await uploadEntryImages(target.id, await filesToPayload(files));
    setSelected(saved);
    selectedRef.current = saved;
    updateRecordList(saved);
    setMessage(`已插入 ${files.length} 张图片`);
  }

  async function commitImages(nextImages: EntryImage[]) {
    const current = selectedRef.current;
    if (!current?.id) return;
    const saved = await updateEntryImages(
      current.id,
      nextImages.map((image) => ({ file_name: image.file_name, label: image.label || "" })),
    );
    setSelected(saved);
    selectedRef.current = saved;
    updateRecordList(saved);
    setMessage(`图片已保存 ${new Date().toLocaleTimeString()}`);
  }

  async function exportAll() {
    try {
      const result = await exportAllEntries();
      window.alert(`已全部导出 ${result.count ?? ""} 篇日记\n\n目录：${result.output_dir}\nWord：${result.docx_path}\nPDF：${result.pdf_path}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "导出失败");
    }
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">日记</h2>
            <Button size="sm" onClick={() => setSelected(newDiary())}>
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
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {records.map((record) => (
            <button
              key={record.id}
              onClick={() => setSelected(record)}
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
                  <span className="text-sm text-muted-foreground">{saving ? "保存中" : message}</span>
                  <Button variant="outline" size="sm" onClick={() => saveCurrent("已手动保存")}>
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
                placeholder="开始写日记..."
                className="min-h-[420px] border-0 resize-none text-base leading-relaxed focus-visible:ring-0"
                value={selected.body || ""}
                onChange={(event) => patch({ body: event.target.value })}
              />
            </div>
            <ImageManager
              images={images}
              onUpload={uploadImages}
              onChange={(nextImages) => patch({ extra: { ...(selected.extra ?? {}), images: nextImages } })}
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
            <select className="h-10 rounded-md border bg-background px-3" value={footprintId} onChange={(event) => setFootprintId(event.target.value)}>
              {footprints.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title}
                </option>
              ))}
            </select>
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
