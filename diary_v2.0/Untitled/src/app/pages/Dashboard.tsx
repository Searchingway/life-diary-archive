import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { AlertCircle, ArrowRight, BookOpen, CheckCircle2, Database, FileText, RefreshCw, Target } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { ModuleKey, Overview, getOverview } from "../lib/api";

const moduleRoutes: Record<ModuleKey, string> = {
  entries: "/diary", footprints: "/footprints", plans: "/light-plan", action_plans: "/action-plan",
  thoughts: "/light-thought", resources: "/light-resource", info_memos: "/order-memo", notes: "/info-memo",
  observations: "/self-observation", lessons: "/lessons-reflection", self_analysis: "/self-analysis", works: "/works-reflection",
};
const quickActions = [
  { label: "写日记", detail: "留住今天的片段", path: "/diary?new=1", icon: BookOpen },
  { label: "记一条信息", detail: "让想法有处可放", path: "/info-memo?new=1", icon: FileText },
  { label: "新建轻计划", detail: "从一个小目标开始", path: "/light-plan?new=1", icon: Target },
  { label: "查看今日任务", detail: "专注下一步行动", path: "/action-plan", icon: CheckCircle2 },
];
const number = new Intl.NumberFormat("zh-CN");

export function Dashboard() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [period, setPeriod] = useState<"month" | "year">("month");
  const requestId = useRef(0);

  async function refresh() {
    const current = ++requestId.current;
    setLoading(true);
    setError("");
    try {
      const data = await getOverview();
      if (current === requestId.current) setOverview(data);
    } catch (cause) {
      if (current === requestId.current) setError(cause instanceof Error ? cause.message : "读取失败，请重试");
    } finally {
      if (current === requestId.current) setLoading(false);
    }
  }
  useEffect(() => {
    void refresh();
    return () => { requestId.current += 1; };
  }, []);

  const stats = overview?.dashboard_stats;
  const month = period === "month";
  const metrics = [
    { label: "日记", unit: "篇", value: month ? stats?.month_diary_count : stats?.year_diary_count },
    { label: "写下的文字", unit: "字", value: month ? stats?.month_diary_words : stats?.year_diary_words },
    { label: "珍藏的图片", unit: "张", value: month ? stats?.month_diary_images : stats?.year_diary_images },
    { label: "完成的计划", unit: "个", value: month ? stats?.month_completed_plans : stats?.year_completed_plans },
  ];
  const total = overview?.modules.reduce((sum, module) => sum + module.count, 0) ?? 0;

  return (
    <div className="min-h-full bg-secondary/20" aria-busy={loading}>
      <div className="mx-auto max-w-6xl space-y-7 p-4 sm:p-6 lg:p-10">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 text-sm text-muted-foreground">{new Date().toLocaleDateString("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" })}</p>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">人生档案工作台</h1>
            <p className="mt-2 text-sm text-muted-foreground">记录生活的细节，也看见自己的积累。</p>
          </div>
          <Button variant="outline" disabled={loading} onClick={() => void refresh()}>
            <RefreshCw className={`size-4 ${loading ? "motion-safe:animate-spin" : ""}`} />{loading ? "读取中…" : "刷新数据"}
          </Button>
        </header>

        {error && <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl border border-destructive/30 bg-background p-4 text-sm">
          <AlertCircle className="size-5 shrink-0 text-destructive" />
          <div className="min-w-0 flex-1"><p className="font-medium">暂时无法读取数据</p><p className="mt-1 break-words text-muted-foreground">{error}{overview ? " · 当前保留上次成功读取的数据" : ""}</p></div>
          <Button size="sm" variant="outline" disabled={loading} onClick={() => void refresh()}>重试</Button>
        </div>}

        <section aria-label="快速记录" className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {quickActions.map(({ label, detail, path, icon: Icon }, index) => <Link key={path} to={path} className={`group flex items-center gap-4 rounded-xl border p-5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring ${index === 0 ? "border-primary bg-primary text-primary-foreground hover:bg-primary/90" : "bg-card hover:bg-accent"}`}>
            <Icon className="size-5 shrink-0" /><div className="min-w-0 flex-1"><p className="font-medium">{label}</p><p className={`mt-1 text-xs ${index === 0 ? "opacity-70" : "text-muted-foreground"}`}>{detail}</p></div><ArrowRight className="size-4 shrink-0 opacity-50 group-hover:opacity-100" />
          </Link>)}
        </section>

        {!overview && loading && <div role="status" className="rounded-xl border bg-card p-8 text-sm text-muted-foreground">正在读取你的本地档案…</div>}

        {overview && <>
          <section aria-label="记录统计" className="rounded-xl border bg-card">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
              <h2 className="font-medium">一点一滴，都算数</h2>
              <div className="flex gap-1 rounded-lg bg-secondary p-1" aria-label="统计时间范围">
                {([["month", "本月"], ["year", "今年"]] as const).map(([value, label]) => <button key={value} type="button" aria-pressed={period === value} onClick={() => setPeriod(value)} className={`rounded-md px-3 py-1 text-sm focus-visible:outline-2 focus-visible:outline-ring ${period === value ? "bg-background font-medium shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>{label}</button>)}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-6 p-5 lg:grid-cols-4 sm:p-6">
              {metrics.map(item => <div key={item.label}><p className="text-xs text-muted-foreground">{item.label}</p><p className="mt-3 text-3xl font-semibold tabular-nums tracking-tight">{number.format(item.value ?? 0)}<span className="ml-2 text-xs font-normal text-muted-foreground">{item.unit}</span></p></div>)}
            </div>
            <Link to="/action-plan" className="flex flex-wrap items-center justify-between gap-3 border-t px-5 py-4 text-sm hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring">
              <span className="flex items-center gap-2"><CheckCircle2 className="size-4" />今日待办 <strong className="tabular-nums">{stats?.today_pending_tasks ?? 0}</strong> 项</span>
              <span className="flex items-center gap-2 text-muted-foreground">{stats?.active_action_plan_count ?? 0} 个进行中 · 共 {stats?.action_plan_count ?? 0} 个行动计划<ArrowRight className="size-4" /></span>
            </Link>
          </section>

          <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
            <Card className="min-w-0">
              <CardHeader><CardTitle>最近动态</CardTitle><CardDescription>继续上次的记录，或看看最近关注的事。</CardDescription></CardHeader>
              <CardContent>
                {overview.recent.length === 0 ? <div className="rounded-lg border border-dashed p-7 text-center"><BookOpen className="mx-auto mb-3 size-6 text-muted-foreground" /><p className="text-sm text-muted-foreground">你的第一条记录，会出现在这里。</p><Button asChild variant="link" className="mt-2"><Link to="/diary?new=1">写下今天</Link></Button></div> : <ul className="divide-y">{overview.recent.slice(0, 8).map(item => <li key={`${item.module_key}-${item.id}`}>
                  <Link to={item.module_key === "entries" ? `/diary?id=${encodeURIComponent(item.id)}` : moduleRoutes[item.module_key]} className="group -mx-2 flex items-center gap-3 rounded-lg px-2 py-4 hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring" aria-label={`${item.module_key === "entries" ? "打开日记" : `前往${item.module}`}：${item.title || "未命名记录"}`}>
                    <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{item.title || "未命名记录"}</p><p className="mt-1.5 text-xs text-muted-foreground">{item.module}<span className="mx-2">·</span>{item.date || item.updated_at?.slice(0, 10) || "未设置日期"}</p></div><ArrowRight className="size-4 shrink-0 text-muted-foreground group-hover:text-foreground" />
                  </Link>
                </li>)}</ul>}
              </CardContent>
            </Card>
            <Card className="min-w-0">
              <CardHeader><CardTitle>我的档案</CardTitle><CardDescription>已积累 {number.format(total)} 条记录</CardDescription></CardHeader>
              <CardContent className="space-y-1">
                {overview.modules.map(module => <Link key={module.key} to={moduleRoutes[module.key]} className="-mx-2 flex items-center justify-between gap-3 rounded-lg px-2 py-2.5 text-sm hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring"><span>{module.label}</span><span className="font-medium tabular-nums text-muted-foreground">{number.format(module.count)}</span></Link>)}
                <div className="mt-4 border-t pt-4"><Button asChild variant="outline" className="w-full"><Link to="/data-management"><Database className="size-4" />备份与数据管理</Link></Button></div>
              </CardContent>
            </Card>
          </div>
        </>}
        <p className="pb-2 text-xs text-muted-foreground">本地档案 · 记录由你掌握</p>
      </div>
    </div>
  );
}
