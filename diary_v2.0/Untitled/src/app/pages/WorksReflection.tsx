import { useEffect, useState } from "react";
import { Download, Film, Plus, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { RecordItem, exportModuleTxt, listRecords, saveRecord } from "../lib/api";

function draftWork(): RecordItem {
  return {
    id: "",
    title: "",
    subtitle: "作品感悟",
    body: "",
    date: "",
    updated_at: "",
    type: "作品",
    extra: { work_type: "作品", creator: "" },
  };
}

export function WorksReflection() {
  const [works, setWorks] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取作品感悟");

  async function load(keyword = query) {
    const data = await listRecords("works", keyword);
    setWorks(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
  }

  useEffect(() => {
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  async function saveSelected() {
    if (!selected) return;
    const saved = await saveRecord("works", selected);
    setSelected(saved);
    setWorks((items) => (items.some((item) => item.id === saved.id) ? items.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...items]));
    setMessage("作品感悟已保存");
  }

  async function exportWorks() {
    try {
      const result = await exportModuleTxt("works");
      window.alert(`作品感悟导出完成，共 ${result.count ?? ""} 条记录\n\n目录：${result.output_dir}\nTXT：${result.txt_path}`);
      setMessage("作品感悟已导出 TXT");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "作品感悟导出失败");
    }
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">作品感悟</h2>
            <Button size="sm" onClick={() => setSelected(draftWork())}>
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索作品..."
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && load(query)}
            />
          </div>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {works.map((work) => (
            <button
              key={work.id}
              onClick={() => setSelected(work)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected?.id === work.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Film className="size-4 mt-1 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{work.title || "未命名作品"}</p>
                  <p className="text-xs opacity-80 mt-1">{String(work.extra?.creator || "未填写作者")}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {selected ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-3 flex-1">
                <Input
                  className="text-3xl font-semibold border-0 px-0 focus-visible:ring-0"
                  placeholder="作品名字"
                  value={selected.title}
                  onChange={(event) => setSelected({ ...selected, title: event.target.value })}
                />
                <div className="grid grid-cols-2 gap-4">
                  <label className="space-y-2">
                    <span className="text-sm text-muted-foreground">作者</span>
                    <Input
                      value={String(selected.extra?.creator || "")}
                      onChange={(event) => setSelected({ ...selected, extra: { ...(selected.extra ?? {}), creator: event.target.value } })}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-sm text-muted-foreground">作品类型</span>
                    <Input value={selected.type || ""} onChange={(event) => setSelected({ ...selected, type: event.target.value })} />
                  </label>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={exportWorks}>
                  <Download className="size-4" />
                  导出 TXT
                </Button>
                <Button onClick={saveSelected}>保存</Button>
              </div>
            </div>

            <Card className="border-2">
              <CardContent className="pt-6">
                <h3 className="text-lg font-medium mb-4">我的感悟</h3>
                <Textarea
                  className="min-h-[360px] text-base leading-relaxed"
                  value={selected.body || ""}
                  onChange={(event) => setSelected({ ...selected, body: event.target.value })}
                  placeholder="记录作品带来的想法、触动和改变。"
                />
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">选择一个作品查看感悟</div>
        )}
      </div>
    </div>
  );
}
