import { useEffect, useState } from "react";
import { Download, FileText, Plus, Search } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { RecordItem, exportModuleTxt, listRecords, saveRecord } from "../lib/api";

const orderTemplate = {
  customer: "",
  intermediary: "",
  executor: "",
  order_date: "",
  deadline: "",
  duration_days: 0,
  price: 0,
  deposit: 0,
  final_payment: 0,
  deliverables: "",
};

function draftMemo(): RecordItem {
  return {
    id: "",
    title: "",
    subtitle: "接单备忘",
    body: "",
    date: new Date().toISOString().slice(0, 10),
    updated_at: "",
    type: "接单记录",
    status: "进行中",
    extra: { info_type: "接单记录", status: "进行中", type_fields: orderTemplate },
  };
}

export function InfoMemo() {
  const [memos, setMemos] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取信息备忘");

  async function load(keyword = query) {
    const data = await listRecords("info_memos", keyword);
    setMemos(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("new")) {
      listRecords("info_memos")
        .then((data) => {
          setMemos(data);
          setSelected(draftMemo());
          setMessage("已创建接单备忘草稿");
        })
        .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
      return;
    }
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  const fields = { ...orderTemplate, ...((selected?.extra?.type_fields as Record<string, unknown>) ?? {}) };

  function patchField(key: string, value: string) {
    if (!selected) return;
    setSelected({ ...selected, extra: { ...(selected.extra ?? {}), type_fields: { ...fields, [key]: value } } });
  }

  async function saveSelected() {
    if (!selected) return;
    const saved = await saveRecord("info_memos", selected);
    setSelected(saved);
    setMemos((items) => (items.some((item) => item.id === saved.id) ? items.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...items]));
    setMessage("信息备忘已保存");
  }

  async function exportMemos() {
    try {
      const result = await exportModuleTxt("info_memos");
      window.alert(`信息备忘导出完成，共 ${result.count ?? ""} 条记录\n\n目录：${result.output_dir}\nTXT：${result.txt_path}`);
      setMessage("信息备忘已导出 TXT");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "信息备忘导出失败");
    }
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">信息备忘</h2>
            <Button size="sm" onClick={() => setSelected(draftMemo())}>
              <Plus className="size-4" />
              接单备忘
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索信息..."
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && load(query)}
            />
          </div>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {memos.map((memo) => (
            <button
              key={memo.id}
              onClick={() => setSelected(memo)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected?.id === memo.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <FileText className="size-4 mt-1 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{memo.title || "未命名备忘"}</p>
                  <p className="text-xs opacity-80 mt-1">{memo.type || memo.subtitle}</p>
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
              <Input
                className="text-3xl font-semibold border-0 px-0 focus-visible:ring-0"
                value={selected.title}
                placeholder="项目 / 订单名称"
                onChange={(event) => setSelected({ ...selected, title: event.target.value })}
              />
              <div className="flex gap-2">
                <Button variant="outline" onClick={exportMemos}>
                  <Download className="size-4" />
                  导出 TXT
                </Button>
                <Button onClick={saveSelected}>保存</Button>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>接单备忘</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-3 gap-4">
                {[
                  ["customer", "客户"],
                  ["intermediary", "中介"],
                  ["executor", "执行人"],
                  ["order_date", "接单日期"],
                  ["deadline", "截止日期"],
                  ["duration_days", "工期"],
                  ["price", "总价"],
                  ["deposit", "定金"],
                  ["final_payment", "尾款"],
                ].map(([key, label]) => (
                  <label className="space-y-2" key={key}>
                    <span className="text-sm text-muted-foreground">{label}</span>
                    <Input value={String(fields[key] ?? "")} onChange={(event) => patchField(key, event.target.value)} />
                  </label>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>交付物</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  className="min-h-[120px]"
                  value={String(fields.deliverables ?? "")}
                  onChange={(event) => patchField("deliverables", event.target.value)}
                  placeholder="列出要交付的内容"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>备注</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  className="min-h-[180px]"
                  value={selected.body || String(selected.extra?.note || "")}
                  onChange={(event) => setSelected({ ...selected, body: event.target.value, extra: { ...(selected.extra ?? {}), note: event.target.value } })}
                />
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">选择一条信息查看详情</div>
        )}
      </div>
    </div>
  );
}
