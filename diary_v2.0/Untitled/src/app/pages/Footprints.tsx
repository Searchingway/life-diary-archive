import { useEffect, useMemo, useState } from "react";
import { Calendar, MapPin, Plus, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { ImageManager } from "../components/records/ImageManager";
import {
  EntryImage,
  FootprintVisit,
  RecordItem,
  listRecords,
  saveFootprintVisit,
  saveRecord,
  updateFootprintVisitImages,
  uploadFootprintVisitImages,
} from "../lib/api";

function cnDate(value: string) {
  if (!value) return "未设置日期";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${year}年${month}月${day}日`;
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

export function Footprints() {
  const [places, setPlaces] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取足迹");
  const visits = useMemo(() => (Array.isArray(selected?.extra?.visits) ? (selected?.extra?.visits as unknown as FootprintVisit[]) : []), [selected]);

  async function load(keyword = query) {
    const data = await listRecords("footprints", keyword);
    setPlaces(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
    setMessage(`已读取 ${data.length} 个地点`);
  }

  useEffect(() => {
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  async function savePlace(patch: Partial<RecordItem>) {
    if (!selected) return;
    const next = { ...selected, ...patch };
    setSelected(next);
    const saved = await saveRecord("footprints", next);
    setSelected(saved);
    setPlaces((items) => items.map((item) => (item.id === saved.id ? saved : item)));
    setMessage("足迹已保存");
  }

  async function addVisit() {
    if (!selected?.id) return;
    const saved = await saveFootprintVisit(selected.id, { date: new Date().toISOString().slice(0, 10) });
    setSelected(saved);
    setPlaces((items) => items.map((item) => (item.id === saved.id ? saved : item)));
  }

  async function uploadVisitImages(visit: FootprintVisit, files: File[]) {
    if (!selected?.id) return;
    const saved = await uploadFootprintVisitImages(selected.id, visit.id, await filesToPayload(files));
    setSelected(saved);
    setPlaces((items) => items.map((item) => (item.id === saved.id ? saved : item)));
    setMessage(`已插入 ${files.length} 张图片`);
  }

  async function commitVisitImages(visit: FootprintVisit, images: EntryImage[]) {
    if (!selected?.id) return;
    const saved = await updateFootprintVisitImages(
      selected.id,
      visit.id,
      images.map((image) => ({ file_name: image.file_name, label: image.label || "" })),
    );
    setSelected(saved);
    setPlaces((items) => items.map((item) => (item.id === saved.id ? saved : item)));
    setMessage("足迹图片已保存");
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">足迹</h2>
            <Button size="sm" onClick={() => setSelected({ id: "", title: "", subtitle: "新地点", body: "", date: "", updated_at: "", extra: { visits: [] } })}>
              <Plus className="size-4" />
              新地点
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索地点..."
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && load(query)}
            />
          </div>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {places.map((place) => (
            <button
              key={place.id}
              onClick={() => setSelected(place)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected?.id === place.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <MapPin className="size-4 mt-1 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{place.title || "未命名地点"}</p>
                  <p className="text-sm opacity-80 mt-1">访问 {Array.isArray(place.extra?.visits) ? place.extra.visits.length : 0} 次</p>
                  <p className="text-xs opacity-80 mt-1">{place.date || place.updated_at?.slice(0, 10)}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {selected ? (
          <div className="p-8 space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-3 flex-1">
                    <Input
                      className="text-2xl font-semibold border-0 px-0 focus-visible:ring-0"
                      value={selected.title}
                      placeholder="地点名称"
                      onChange={(event) => setSelected({ ...selected, title: event.target.value })}
                      onBlur={() => savePlace({ title: selected.title })}
                    />
                    <p className="text-muted-foreground">共访问 {visits.length} 次</p>
                  </div>
                  <Button variant="outline" onClick={() => savePlace({ body: selected.body })}>
                    保存地点
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Textarea
                  className="min-h-[110px]"
                  placeholder="地点描述"
                  value={selected.body || ""}
                  onChange={(event) => setSelected({ ...selected, body: event.target.value })}
                  onBlur={() => savePlace({ body: selected.body })}
                />
              </CardContent>
            </Card>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">访问记录</h3>
                <Button size="sm" onClick={addVisit} disabled={!selected.id}>
                  <Plus className="size-4" />
                  新访问
                </Button>
              </div>
              <div className="space-y-4">
                {visits.length === 0 && <div className="text-sm text-muted-foreground">还没有访问记录。</div>}
                {visits.map((visit) => (
                  <Card key={visit.id}>
                    <CardContent className="pt-6">
                      <div className="flex items-center gap-3 mb-4 text-primary">
                        <Calendar className="size-5" />
                        <h4 className="font-semibold">{cnDate(visit.date)}</h4>
                      </div>
                      {visit.thought && <p className="text-muted-foreground mb-4 whitespace-pre-wrap">{visit.thought}</p>}
                    </CardContent>
                    <ImageManager
                      images={visit.images ?? []}
                      onUpload={(files) => uploadVisitImages(visit, files)}
                      onChange={(nextImages) => {
                        const nextVisits = visits.map((item) => (item.id === visit.id ? { ...item, images: nextImages } : item));
                        setSelected({ ...selected, extra: { ...(selected.extra ?? {}), visits: nextVisits } });
                      }}
                      onCommit={(nextImages) => commitVisitImages(visit, nextImages)}
                    />
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">选择一个地点查看访问记录</div>
        )}
      </div>
    </div>
  );
}
