import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { ArrowRight, CheckCircle, Download, Plus, Search, Sparkles, Target } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { RecordItem, exportModuleTxt, listRecords, promoteLightPlan, saveRecord } from "../lib/api";

function draftPlan(): RecordItem {
  return {
    id: "",
    title: "",
    subtitle: "新计划",
    body: "",
    date: new Date().toISOString().slice(0, 10),
    updated_at: "",
    type: "add",
    status: "进行中",
    extra: { plan_type: "add" },
  };
}

export function LightPlan() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [filter, setFilter] = useState<"all" | "add" | "reduce" | "completed">("all");
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取轻计划");
  const selectedPlanType = String(selected?.extra?.plan_type || selected?.type || "add");

  async function load(keyword = query) {
    const data = await listRecords("plans", keyword);
    setPlans(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("new")) {
      listRecords("plans")
        .then((data) => {
          setPlans(data);
          setSelected(draftPlan());
          setMessage("已创建轻计划草稿");
        })
        .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
      return;
    }
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  const filtered = plans.filter((plan) => {
    const type = String(plan.type || plan.extra?.plan_type || "");
    if (filter === "all") return true;
    if (filter === "completed") return String(plan.status || "").includes("完成");
    if (filter === "add") return type.includes("add") || type.includes("增");
    return type.includes("reduce") || type.includes("减");
  });

  async function saveSelected() {
    if (!selected) return null;
    const saved = await saveRecord("plans", selected);
    setSelected(saved);
    setPlans((items) => (items.some((item) => item.id === saved.id) ? items.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...items]));
    setMessage("轻计划已保存");
    return saved;
  }

  async function promote() {
    let target = selected;
    if (!target?.id) {
      target = await saveSelected();
    }
    if (!target?.id) return;
    await promoteLightPlan(target.id);
    setMessage("已迁移到行动计划");
    navigate("/action-plan");
  }

  async function exportPlans() {
    try {
      const result = await exportModuleTxt("plans");
      window.alert(`轻计划导出完成，共 ${result.count ?? ""} 条记录\n\n目录：${result.output_dir}\nTXT：${result.txt_path}`);
      setMessage("轻计划已导出 TXT");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "轻计划导出失败");
    }
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">轻计划</h2>
            <Button size="sm" onClick={() => setSelected(draftPlan())}>
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索计划..."
              className="pl-9"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && load(query)}
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              ["all", "全部"],
              ["add", "增量"],
              ["reduce", "减量"],
              ["completed", "已完成"],
            ].map(([key, label]) => (
              <Button key={key} variant={filter === key ? "default" : "outline"} size="sm" onClick={() => setFilter(key as typeof filter)}>
                {label}
              </Button>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {filtered.map((plan) => (
            <button
              key={plan.id}
              onClick={() => setSelected(plan)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selected?.id === plan.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Target className="size-4 mt-1 shrink-0" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{plan.title || "未命名计划"}</p>
                  <p className="text-xs opacity-80 mt-2">{plan.type || plan.status || "轻计划"}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {selected ? (
          <div className="p-8 max-w-4xl space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div className="space-y-3 flex-1">
                <Input
                  className="text-3xl font-semibold border-0 px-0 focus-visible:ring-0"
                  placeholder="计划标题"
                  value={selected.title}
                  onChange={(event) => setSelected({ ...selected, title: event.target.value })}
                />
                <div className="flex items-center gap-2">
                  <div className="flex h-11 rounded-lg border bg-background p-1 shrink-0">
                    <Button
                      type="button"
                      size="sm"
                      variant={selectedPlanType === "add" || selectedPlanType.includes("增") ? "default" : "ghost"}
                      className="h-8"
                      onClick={() => setSelected({ ...selected, type: "add", extra: { ...(selected.extra ?? {}), plan_type: "add" } })}
                    >
                      增量计划
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant={selectedPlanType === "reduce" || selectedPlanType.includes("减") ? "default" : "ghost"}
                      className="h-8"
                      onClick={() => setSelected({ ...selected, type: "reduce", extra: { ...(selected.extra ?? {}), plan_type: "reduce" } })}
                    >
                      减量计划
                    </Button>
                  </div>
                  <Input className="w-40" value={selected.date || ""} onChange={(event) => setSelected({ ...selected, date: event.target.value })} />
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={exportPlans}>
                  <Download className="size-4" />
                  导出 TXT
                </Button>
                <Button variant="outline" onClick={saveSelected}>
                  保存
                </Button>
                <Button onClick={promote}>
                  <Sparkles className="size-4" />
                  详细分析
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="pt-6 space-y-4">
                <label className="space-y-2 block">
                  <span className="font-medium">计划内容</span>
                  <Textarea
                    className="min-h-[260px] text-base leading-relaxed"
                    value={selected.body || ""}
                    onChange={(event) => setSelected({ ...selected, body: event.target.value })}
                    placeholder="写下想增加的行动、想减少的行为、原因和替代方案。"
                  />
                </label>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={saveSelected}>
                    <CheckCircle className="size-4" />
                    保存轻计划
                  </Button>
                  <Button variant="outline" onClick={promote}>
                    <ArrowRight className="size-4" />
                    转为行动计划
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">选择一个计划查看详情</div>
        )}
      </div>
    </div>
  );
}
