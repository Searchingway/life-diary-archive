import { useEffect, useMemo, useState } from "react";
import { LucideIcon, Plus, Save, Search, Trash2 } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import { ModuleKey, RecordItem, deleteRecord, listRecords, saveRecord } from "../../lib/api";

const resourceLabels = ["时间", "金钱", "精力", "情绪", "勇气", "身体", "注意力", "风险", "机会成本"];

interface RecordModulePageProps {
  moduleKey: ModuleKey;
  title: string;
  icon: LucideIcon;
  description: string;
  bodyLabel?: string;
  dateLabel?: string;
  readOnly?: boolean;
}

function createDraft(moduleKey: ModuleKey, title: string): RecordItem {
  const today = new Date().toISOString().slice(0, 10);
  return {
    id: "",
    title: "",
    subtitle: "新建草稿",
    body: "",
    date: today,
    updated_at: "",
    status: "",
    type: "",
    extra:
      moduleKey === "resources"
        ? {
            resource_items: resourceLabels.map((label) => ({ type: label, value: "" })),
            recurrence_test: {},
            overall_judgement: "",
          }
        : {},
  };
}

export function RecordModulePage({
  moduleKey,
  title,
  icon: Icon,
  description,
  bodyLabel = "内容",
  dateLabel = "日期",
  readOnly = false,
}: RecordModulePageProps) {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取旧版数据");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const selectedIndex = useMemo(
    () => records.findIndex((record) => record.id && record.id === selected?.id),
    [records, selected],
  );

  async function load(keyword = query) {
    setLoading(true);
    try {
      const nextRecords = await listRecords(moduleKey, keyword);
      setRecords(nextRecords);
      setSelected((current) => {
        if (current?.id) {
          return nextRecords.find((item) => item.id === current.id) ?? nextRecords[0] ?? null;
        }
        return nextRecords[0] ?? null;
      });
      setMessage(`已迁移并读取 ${nextRecords.length} 条${title}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "读取失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load("");
  }, [moduleKey]);

  function patchSelected(patch: Partial<RecordItem>) {
    setSelected((current) => (current ? { ...current, ...patch } : current));
  }

  function patchExtra(patch: Record<string, unknown>) {
    setSelected((current) =>
      current ? { ...current, extra: { ...(current.extra ?? {}), ...patch } } : current,
    );
  }

  async function saveCurrent() {
    if (!selected || readOnly) return;
    setSaving(true);
    try {
      const saved = await saveRecord(moduleKey, selected);
      setSelected(saved);
      await load(query);
      setMessage("已保存到 2.0 数据目录");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function deleteCurrent() {
    if (!selected?.id || readOnly) return;
    const confirmed = window.confirm(`确定删除这条${title}吗？`);
    if (!confirmed) return;
    try {
      await deleteRecord(moduleKey, selected.id);
      setSelected(null);
      await load(query);
      setMessage("已删除");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "删除失败");
    }
  }

  function addDraft() {
    const draft = createDraft(moduleKey, title);
    setSelected(draft);
    setRecords((items) => [draft, ...items]);
    setMessage("已创建草稿，填写后点击保存");
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">{title}</h2>
            {!readOnly && (
              <Button size="sm" onClick={addDraft}>
                <Plus className="size-4" />
                新建
              </Button>
            )}
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder={`搜索${title}...`}
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") load(query);
              }}
            />
          </div>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {loading && <p className="p-3 text-sm text-muted-foreground">正在加载...</p>}
          {!loading && records.length === 0 && <p className="p-3 text-sm text-muted-foreground">暂无记录</p>}
          {records.map((record, index) => (
            <button
              key={record.id || `draft-${index}`}
              onClick={() => setSelected(record)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected === record || selectedIndex === index
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Icon className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs opacity-80 mb-1">{record.date || record.updated_at?.slice(0, 10) || "未设置日期"}</p>
                  <p className="font-medium truncate">{record.title || "未命名记录"}</p>
                  <p className="text-sm opacity-80 truncate mt-1">{record.subtitle || record.status || record.type || "本地记录"}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {selected ? (
          <div className="p-8 max-w-5xl space-y-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <Input
                  value={selected.title}
                  onChange={(event) => patchSelected({ title: event.target.value })}
                  readOnly={readOnly}
                  placeholder={`${title}标题`}
                  className="text-3xl font-semibold border-0 px-0 focus-visible:ring-0"
                />
                <p className="text-muted-foreground">{description}</p>
              </div>
              {!readOnly && (
                <div className="flex gap-2">
                  <Button variant="outline" onClick={deleteCurrent} disabled={!selected.id}>
                    <Trash2 className="size-4" />
                    删除
                  </Button>
                  <Button onClick={saveCurrent} disabled={saving}>
                    <Save className="size-4" />
                    {saving ? "保存中" : "保存"}
                  </Button>
                </div>
              )}
            </div>

            <Card>
              <CardContent className="pt-6 space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <label className="space-y-2">
                    <span className="text-sm text-muted-foreground">{dateLabel}</span>
                    <Input
                      value={selected.date || ""}
                      onChange={(event) => patchSelected({ date: event.target.value })}
                      readOnly={readOnly}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-sm text-muted-foreground">类型</span>
                    <Input
                      value={selected.type || ""}
                      onChange={(event) => patchSelected({ type: event.target.value })}
                      readOnly={readOnly}
                    />
                  </label>
                  <label className="space-y-2">
                    <span className="text-sm text-muted-foreground">状态</span>
                    <Input
                      value={selected.status || ""}
                      onChange={(event) => patchSelected({ status: event.target.value })}
                      readOnly={readOnly}
                    />
                  </label>
                </div>
                <label className="space-y-2 block">
                  <span className="text-sm text-muted-foreground">{bodyLabel}</span>
                  <Textarea
                    value={selected.body || ""}
                    onChange={(event) => patchSelected({ body: event.target.value })}
                    readOnly={readOnly}
                    className="min-h-[300px] text-base leading-relaxed"
                    placeholder="从旧版迁移过来的内容会显示在这里..."
                  />
                </label>
              </CardContent>
            </Card>

            {moduleKey === "resources" && (
              <ResourceCostEditor selected={selected} patchExtra={patchExtra} readOnly={readOnly} />
            )}
            {moduleKey === "action_plans" && <ActionPlanPreview selected={selected} />}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Icon className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一条{title}查看详情</p>
              {!readOnly && <p className="text-sm mt-2">或创建新记录</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ResourceCostEditor({
  selected,
  patchExtra,
  readOnly,
}: {
  selected: RecordItem;
  patchExtra: (patch: Record<string, unknown>) => void;
  readOnly: boolean;
}) {
  const extra = selected.extra ?? {};
  const items = Array.isArray(extra.resource_items)
    ? extra.resource_items
    : resourceLabels.map((label) => ({ type: label, value: "" }));

  function updateCost(index: number, value: string) {
    const nextItems = resourceLabels.map((label, itemIndex) => {
      const item = items[itemIndex];
      const base = typeof item === "object" && item ? (item as Record<string, unknown>) : {};
      return { ...base, type: String(base.type || label), value: itemIndex === index ? value : String(base.value || "") };
    });
    patchExtra({ resource_items: nextItems });
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">资源消耗评估</h3>
      <div className="grid grid-cols-3 gap-4">
        {resourceLabels.map((label, index) => {
          const item = items[index] as Record<string, unknown> | undefined;
          return (
            <Card key={label}>
              <CardHeader>
                <CardTitle className="text-base">{String(item?.type || label)}</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={String(item?.value || item?.description || "")}
                  onChange={(event) => updateCost(index, event.target.value)}
                  readOnly={readOnly}
                  className="min-h-[80px]"
                  placeholder={`记录${label}方面的消耗`}
                />
              </CardContent>
            </Card>
          );
        })}
      </div>
      <Card className="mt-6 border-2 border-primary">
        <CardContent className="pt-6 space-y-4">
          <label className="space-y-2 block">
            <span className="font-medium">综合判断</span>
            <Textarea
              value={String(extra.overall_judgement || "")}
              readOnly={readOnly}
              onChange={(event) => patchExtra({ overall_judgement: event.target.value })}
              className="min-h-[90px]"
            />
          </label>
        </CardContent>
      </Card>
    </div>
  );
}

function ActionPlanPreview({ selected }: { selected: RecordItem }) {
  const tasks = Array.isArray(selected.extra?.tasks) ? selected.extra.tasks : [];
  const completed = tasks.filter((task) => typeof task === "object" && task && (task as Record<string, unknown>).done).length;
  const progress = tasks.length ? Math.round((completed / tasks.length) * 100) : 0;

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-secondary rounded-full h-2">
            <div className="bg-primary h-2 rounded-full" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-sm font-medium">{progress}%</span>
        </div>
        <div className="space-y-3">
          {tasks.slice(0, 20).map((task, index) => {
            const item = task as Record<string, unknown>;
            return (
              <div key={String(item.id || index)} className="flex items-start gap-3 p-3 rounded-lg border">
                <input type="checkbox" checked={Boolean(item.done)} readOnly className="mt-1" />
                <div>
                  <p className={item.done ? "font-medium line-through" : "font-medium"}>{String(item.title || "未命名任务")}</p>
                  <p className="text-sm text-muted-foreground">{String(item.date || "")}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
