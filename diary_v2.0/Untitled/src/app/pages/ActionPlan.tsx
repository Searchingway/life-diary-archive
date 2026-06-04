import { useEffect, useReducer } from "react";
import { Calendar, CheckCircle, GanttChart, List, Network, Plus, Search, Trash2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { RecordItem, exportModuleTxt, listRecords, saveRecord } from "../lib/api";
import {
  ActionPlanTaskV2,
  ActionPlanView,
  LegacyTask,
  createEmptyTask,
  ganttBarDays,
  groupTasksByDate,
  sortDateKeys,
  toActionPlanTaskV2,
} from "../types/actionPlan";

// ── State ──

interface ActionPlanState {
  plans: RecordItem[];
  selectedPlanId: string | null;
  currentView: ActionPlanView;
  query: string;
  loading: boolean;
  error: string | null;
  message: string;
}

const initialState: ActionPlanState = {
  plans: [],
  selectedPlanId: null,
  currentView: "today",
  query: "",
  loading: true,
  error: null,
  message: "正在读取行动计划",
};

type ActionPlanEvent =
  | { type: "INIT_PAGE" }
  | { type: "LOAD_SUCCESS"; plans: RecordItem[] }
  | { type: "LOAD_FAILED"; message: string }
  | { type: "SELECT_PLAN"; planId: string }
  | { type: "SWITCH_VIEW"; view: ActionPlanView }
  | { type: "CHANGE_QUERY"; query: string }
  | { type: "SAVE_SUCCESS"; plan: RecordItem }
  | { type: "SAVE_FAILED"; message: string }
  | { type: "SET_MESSAGE"; message: string };

function actionPlanReducer(state: ActionPlanState, event: ActionPlanEvent): ActionPlanState {
  switch (event.type) {
    case "INIT_PAGE":
      return { ...state, loading: true, error: null };
    case "LOAD_SUCCESS":
      const plans = event.plans;
      return {
        ...state,
        loading: false,
        error: null,
        plans,
        selectedPlanId: plans.length > 0 ? plans[0].id : null,
        currentView: "today",
      };
    case "LOAD_FAILED":
      return { ...state, loading: false, error: event.message };
    case "SELECT_PLAN":
      if (event.planId === state.selectedPlanId) return state;
      return { ...state, selectedPlanId: event.planId, currentView: "today" };
    case "SWITCH_VIEW":
      if (!state.selectedPlanId) return state;
      return { ...state, currentView: event.view };
    case "CHANGE_QUERY":
      return { ...state, query: event.query };
    case "SAVE_SUCCESS":
      const saved = event.plan;
      const idx = state.plans.findIndex((p) => p.id === saved.id);
      const newPlans = idx >= 0 ? state.plans.map((p, i) => (i === idx ? saved : p)) : [saved, ...state.plans];
      return { ...state, plans: newPlans, selectedPlanId: saved.id };
    case "SAVE_FAILED":
      return { ...state, error: event.message };
    case "SET_MESSAGE":
      return { ...state, message: event.message };
    default:
      return state;
  }
}

// ── Helpers ──

function extractTasks(plan: RecordItem): ActionPlanTaskV2[] {
  const raw = plan?.extra?.tasks as LegacyTask[] | undefined;
  return Array.isArray(raw) ? raw.map(toActionPlanTaskV2) : [];
}

function planProgress(tasks: ActionPlanTaskV2[]): number {
  if (tasks.length === 0) return 0;
  return Math.round((tasks.filter((t) => t.done).length / tasks.length) * 100);
}

function cnDate(value: string) {
  if (!value) return "未设置日期";
  const [y, m, d] = value.slice(0, 10).split("-");
  return `${y}年${m}月${d}日`;
}

// ── Component ──

export function ActionPlan() {
  const [state, dispatch] = useReducer(actionPlanReducer, initialState);

  const selectedPlan = state.plans.find((p) => p.id === state.selectedPlanId) ?? null;
  const tasks = extractTasks(selectedPlan!);
  const progress = planProgress(tasks);
  const grouped = groupTasksByDate(tasks);
  const sortedDates = sortDateKeys(grouped);
  const today = new Date().toISOString().slice(0, 10);

  // Load
  async function load(keyword = state.query) {
    dispatch({ type: "INIT_PAGE" });
    try {
      const data = await listRecords("action_plans", keyword);
      dispatch({ type: "LOAD_SUCCESS", plans: data });
    } catch (err) {
      dispatch({ type: "LOAD_FAILED", message: err instanceof Error ? err.message : "加载失败" });
    }
  }

  useEffect(() => {
    load("");
  }, []);

  // Save
  async function savePlanTasks(plan: RecordItem, nextTasks: ActionPlanTaskV2[]) {
    const updated: RecordItem = { ...plan, extra: { ...(plan.extra ?? {}), tasks: nextTasks } };
    try {
      const saved = await saveRecord("action_plans", updated);
      dispatch({ type: "SAVE_SUCCESS", plan: saved });
      dispatch({ type: "SET_MESSAGE", message: `已保存 ${new Date().toLocaleTimeString()}` });
    } catch (err) {
      dispatch({ type: "SAVE_FAILED", message: err instanceof Error ? err.message : "保存失败" });
    }
  }

  async function savePlanTitle(plan: RecordItem, title: string) {
    const updated: RecordItem = { ...plan, title };
    try {
      const saved = await saveRecord("action_plans", updated);
      dispatch({ type: "SAVE_SUCCESS", plan: saved });
    } catch (err) {
      dispatch({ type: "SET_MESSAGE", message: err instanceof Error ? err.message : "保存失败" });
    }
  }

  function toggleTaskDone(taskId: string) {
    if (!selectedPlan) return;
    const nextTasks = tasks.map((t) =>
      t.id === taskId ? { ...t, done: !t.done, progress: !t.done ? 100 : 0, status: !t.done ? ("done" as const) : ("todo" as const) } : t,
    );
    savePlanTasks(selectedPlan, nextTasks);
  }

  function addTask() {
    if (!selectedPlan) return;
    const planStartDate = String(selectedPlan.extra?.start_date || selectedPlan.extra?.startDate || selectedPlan.date || today);
    const newTask = createEmptyTask(planStartDate);
    savePlanTasks(selectedPlan, [...tasks, newTask]);
  }

  function removeTask(taskId: string) {
    if (!selectedPlan) return;
    const nextTasks = tasks.filter((t) => t.id !== taskId).map((t) => ({ ...t, dependsOn: t.dependsOn.filter((d) => d !== taskId) }));
    savePlanTasks(selectedPlan, nextTasks);
  }

  // Exports
  async function handleExport() {
    try {
      const result = await exportModuleTxt("action_plans");
      dispatch({ type: "SET_MESSAGE", message: `行动计划导出完成，${result.count ?? ""} 条记录` });
    } catch (err) {
      dispatch({ type: "SET_MESSAGE", message: err instanceof Error ? err.message : "导出失败" });
    }
  }

  // ── Render ──

  if (state.loading) {
    return (
      <div className="h-full grid place-content-center text-muted-foreground">
        <p>{state.message}</p>
      </div>
    );
  }

  if (state.plans.length === 0) {
    return (
      <div className="h-full grid place-content-center gap-3 text-center text-muted-foreground">
        <CheckCircle className="size-12 mx-auto opacity-40" />
        <p className="text-lg">还没有行动计划</p>
        <Button
          onClick={() => {
            const plan: RecordItem = { id: "", title: "新行动计划", subtitle: "", body: "", date: today, updated_at: "", type: "其他", status: "进行中", extra: { plan_type: "其他", tasks: [] } };
            savePlanTasks(plan, []).then(() => dispatch({ type: "SET_MESSAGE", message: "已创建行动计划草稿" }));
          }}
        >
          <Plus className="size-4" /> 新建行动计划
        </Button>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      {/* ── Sidebar ── */}
      <div className="w-72 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">行动计划</h2>
            <Button size="sm" onClick={addPlanViaSave}>
              <Plus className="size-4" />
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input
              placeholder="搜索计划..."
              className="pl-9"
              value={state.query}
              onChange={(e) => dispatch({ type: "CHANGE_QUERY", query: e.target.value })}
              onKeyDown={(e) => e.key === "Enter" && load(state.query)}
            />
          </div>
          <p className="text-xs text-muted-foreground">{state.message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {state.plans.map((plan) => {
            const pt = extractTasks(plan);
            const pct = planProgress(pt);
            return (
              <button
                key={plan.id}
                onClick={() => dispatch({ type: "SELECT_PLAN", planId: plan.id })}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  state.selectedPlanId === plan.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
                }`}
              >
                <p className="font-medium truncate text-sm">{plan.title || "未命名行动计划"}</p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 bg-secondary rounded-full h-1">
                    <div className="bg-green-500 h-1 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs">{pct}%</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Main Area ── */}
      <div className="flex-1 flex flex-col">
        {selectedPlan ? (
          <>
            {/* Plan Header */}
            <div className="border-b p-4 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <Input
                      className="text-xl font-semibold border-0 px-0 focus-visible:ring-0 h-auto"
                      value={selectedPlan.title}
                      placeholder="行动计划标题"
                      onBlur={(e) => {
                        if (e.target.value !== selectedPlan.title) savePlanTitle(selectedPlan, e.target.value);
                      }}
                      onChange={(e) => {
                        selectedPlan.title = e.target.value;
                      }}
                    />
                    <span className="text-xs px-2 py-0.5 rounded bg-secondary">{String(selectedPlan.extra?.plan_type || selectedPlan.type || "其他")}</span>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-muted-foreground">
                    <span>{selectedPlan.status || "进行中"}</span>
                    <span>·</span>
                    <span>{String(selectedPlan.extra?.start_date || selectedPlan.date || "")} ~ {String(selectedPlan.extra?.end_date || "")}</span>
                    <span>·</span>
                    <span>{tasks.filter((t) => t.done).length}/{tasks.length} 完成</span>
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button variant="outline" size="sm" onClick={handleExport}>导出 TXT</Button>
                  <Button size="sm" onClick={addTask}><Plus className="size-4" /> 添加任务</Button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-40 bg-secondary rounded-full h-1.5">
                  <div className="bg-primary h-1.5 rounded-full" style={{ width: `${progress}%` }} />
                </div>
                <span className="text-xs font-medium">{progress}%</span>
              </div>
            </div>

            {/* View Tabs */}
            <div className="flex items-center border-b px-4">
              {(["today", "gantt", "chain"] as ActionPlanView[]).map((v) => {
                const icons: Record<ActionPlanView, React.ReactNode> = { today: <List className="size-4" />, gantt: <GanttChart className="size-4" />, chain: <Network className="size-4" /> };
                const labels: Record<ActionPlanView, string> = { today: "时间表", gantt: "甘特图", chain: "任务链" };
                return (
                  <button
                    key={v}
                    onClick={() => dispatch({ type: "SWITCH_VIEW", view: v })}
                    className={`flex items-center gap-1.5 px-4 py-2 text-sm border-b-2 transition-colors ${
                      state.currentView === v ? "border-primary text-primary font-medium" : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {icons[v]} {labels[v]}
                  </button>
                );
              })}
            </div>

            {/* View Content */}
            <div className="flex-1 overflow-y-auto">
              {state.currentView === "today" && <TodayView tasks={tasks} grouped={grouped} sortedDates={sortedDates} today={today} onToggle={toggleTaskDone} onRemove={removeTask} />}
              {state.currentView === "gantt" && <GanttView tasks={tasks} today={today} />}
              {state.currentView === "chain" && <ChainView tasks={tasks} today={today} />}
            </div>

            {state.error && <div className="border-t p-3 text-sm text-red-600 bg-red-50">{state.error}</div>}
          </>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">从左侧选择一个行动计划</div>
        )}
      </div>
    </div>
  );

  async function addPlanViaSave() {
    const plan: RecordItem = {
      id: "",
      title: "新行动计划",
      subtitle: "",
      body: "",
      date: today,
      updated_at: "",
      type: "其他",
      status: "进行中",
      extra: { plan_type: "其他", tasks: [], start_date: today },
    };
    try {
      const saved = await saveRecord("action_plans", plan);
      dispatch({ type: "SAVE_SUCCESS", plan: saved });
      dispatch({ type: "SET_MESSAGE", message: "已创建行动计划草稿" });
    } catch (err) {
      dispatch({ type: "SAVE_FAILED", message: err instanceof Error ? err.message : "新建失败" });
    }
  }
}

// ── Today View ──

function TodayView({
  tasks,
  grouped,
  sortedDates,
  today,
  onToggle,
  onRemove,
}: {
  tasks: ActionPlanTaskV2[];
  grouped: Record<string, ActionPlanTaskV2[]>;
  sortedDates: string[];
  today: string;
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
}) {
  if (tasks.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-16">
        <CheckCircle className="size-10 mx-auto mb-3 opacity-40" />
        还没有子任务，点击"添加任务"开始
      </div>
    );
  }

  return (
    <div className="p-4 space-y-6">
      {sortedDates.map((date) => {
        const dateTasks = grouped[date];
        const isToday = date === today;
        const isOverdue = date < today && dateTasks.some((t) => !t.done);
        return (
          <div key={date}>
            <div className="flex items-center gap-2 mb-2">
              <Calendar className={`size-4 ${isToday ? "text-primary" : "text-muted-foreground"}`} />
              <h3 className={`font-semibold text-sm ${isToday ? "text-primary" : ""}`}>{cnDate(date)}</h3>
              {isToday && <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">今天</span>}
              {isOverdue && <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 font-medium">逾期</span>}
            </div>
            <div className="space-y-2">
              {dateTasks.map((task) => (
                <Card key={task.id} className={task.done ? "opacity-60" : ""}>
                  <CardContent className="p-3">
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        className="mt-1"
                        checked={task.done}
                        onChange={() => onToggle(task.id)}
                      />
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm ${task.done ? "line-through text-muted-foreground" : ""}`}>{task.title}</p>
                        <div className="flex gap-3 mt-1 text-xs text-muted-foreground">
                          {task.estimatedMinutes > 0 && <span>{task.estimatedMinutes} 分钟</span>}
                          {task.note && <span className="truncate">{task.note}</span>}
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => onRemove(task.id)}><Trash2 className="size-3" /></Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Gantt View (Static) ──

function GanttView({ tasks, today }: { tasks: ActionPlanTaskV2[]; today: string }) {
  if (tasks.length === 0) {
    return <div className="text-center text-muted-foreground py-16">还没有子任务</div>;
  }

  // Find date range
  const dates = tasks.flatMap((t) => [t.startDate, t.endDate].filter(Boolean));
  if (dates.length === 0) dates.push(today);
  const allDates = [...new Set(dates)].sort();
  const minDate = allDates[0];
  const maxDate = allDates[allDates.length - 1];

  // Generate day columns
  const dayColumns: string[] = [];
  const cursor = new Date(minDate);
  const end = new Date(maxDate);
  while (cursor <= end) {
    dayColumns.push(cursor.toISOString().slice(0, 10));
    cursor.setDate(cursor.getDate() + 1);
  }

  const colWidth = 36; // px per day column

  if (dayColumns.length === 0) return <div className="text-center text-muted-foreground py-16">无法确定日期范围</div>;

  return (
    <div className="p-4">
      <div className="overflow-x-auto border rounded-lg">
        {/* Header: task list + date axis */}
        <div className="flex" style={{ minWidth: 200 + dayColumns.length * colWidth }}>
          {/* Task list column */}
          <div className="w-[200px] shrink-0 border-r bg-muted/30 p-2">
            <p className="text-xs font-medium text-muted-foreground">任务</p>
          </div>
          {/* Date axis */}
          <div className="flex">
            {dayColumns.map((d) => {
              const isToday = d === today;
              return (
                <div key={d} className={`text-center text-[10px] p-1 border-r ${isToday ? "bg-primary/10 text-primary font-semibold" : "text-muted-foreground"}`} style={{ width: colWidth }}>
                  {d.slice(5)}
                </div>
              );
            })}
          </div>
        </div>

        {/* Task bars */}
        {tasks.map((task) => {
          const startIdx = dayColumns.indexOf(task.startDate);
          const endIdx = dayColumns.indexOf(task.endDate);
          const left = startIdx >= 0 ? startIdx * colWidth : 0;
          const days = ganttBarDays(task);
          const width = Math.max(colWidth, days * colWidth);
          const isToday = task.startDate <= today && task.endDate >= today;

          return (
            <div key={task.id} className="flex border-t" style={{ minWidth: 200 + dayColumns.length * colWidth }}>
              <div className="w-[200px] shrink-0 border-r p-2">
                <p className={`text-xs truncate ${task.done ? "line-through text-muted-foreground" : ""}`}>{task.title}</p>
                <p className="text-[10px] text-muted-foreground">{task.estimatedMinutes} 分钟</p>
              </div>
              <div className="relative flex-1" style={{ height: 36 }}>
                {/* Background grid for today */}
                {isToday && (
                  <div className="absolute inset-y-0 bg-primary/5" style={{ left, width: Math.max(colWidth, days * colWidth) }} />
                )}
                {/* Bar */}
                <div
                  className={`absolute top-1.5 h-6 rounded-sm border ${task.done ? "bg-green-200 border-green-400" : "bg-blue-200 border-blue-400"}`}
                  style={{ left, width }}
                >
                  {/* Progress fill */}
                  {task.progress > 0 && (
                    <div
                      className={`h-full rounded-sm ${task.done ? "bg-green-400" : "bg-blue-400"}`}
                      style={{ width: `${task.progress}%` }}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        甘特图 — 条宽 = endDate - startDate + 1 天。estimatedMinutes 仅显示在左侧。
      </p>
    </div>
  );
}

// ── Chain View (Static) ──

function ChainView({ tasks, today: _today }: { tasks: ActionPlanTaskV2[]; today: string }) {
  if (tasks.length === 0) {
    return <div className="text-center text-muted-foreground py-16">还没有子任务</div>;
  }

  // Group by date, auto-layout in columns
  const byDate: Record<string, ActionPlanTaskV2[]> = {};
  for (const t of tasks) {
    const key = t.startDate || "未安排";
    (byDate[key] ??= []).push(t);
  }
  const dates = Object.keys(byDate).sort();

  const colW = 120;
  const rowH = 60;

  return (
    <div className="p-4 overflow-auto" style={{ background: "#16181c", minHeight: 300 }}>
      <svg
        width={dates.length * colW + 80}
        height={Math.max(tasks.length, 1) * rowH + 80}
        style={{ display: "block" }}
      >
        {/* Draw dependency lines */}
        {tasks.map((task) => {
          const fromCol = dates.indexOf(task.startDate || "未安排");
          return task.dependsOn.map((depId) => {
            const dep = tasks.find((t) => t.id === depId);
            if (!dep) return null;
            const toCol = dates.indexOf(dep.startDate || "未安排");
            const fromIdx = byDate[task.startDate || "未安排"]?.indexOf(task) ?? 0;
            const toIdx = byDate[dep.startDate || "未安排"]?.indexOf(dep) ?? 0;
            const x1 = fromCol * colW + 100;
            const y1 = 40 + fromIdx * rowH + 15;
            const x2 = toCol * colW + 100;
            const y2 = 40 + toIdx * rowH + 15;
            return (
              <line key={`${task.id}-${depId}`} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#444" strokeWidth={1.5} strokeDasharray="4 2" />
            );
          });
        })}

        {/* Draw date columns */}
        {dates.map((date, colIdx) => {
          const cx = colIdx * colW + 80;
          return (
            <g key={date}>
              <text x={cx} y={20} fill="#888" fontSize={11} textAnchor="middle">{date}</text>
              <line x1={cx} y1={30} x2={cx} y2={30 + (byDate[date].length - 1) * rowH + 20} stroke="#333" strokeWidth={2} />
              {byDate[date].map((task, rowIdx) => {
                const cy = 40 + rowIdx * rowH;
                const color = task.done ? "#4ade80" : "#60a5fa";
                const r = 16;
                return (
                  <g key={task.id}>
                    <circle cx={cx} cy={cy} r={r} fill={color} fillOpacity={0.3} stroke={color} strokeWidth={2} />
                    <text x={cx} y={cy + 4} fill="#fff" fontSize={9} textAnchor="middle" dominantBaseline="middle">
                      {task.title.length > 6 ? task.title.slice(0, 5) + ".." : task.title}
                    </text>
                    <title>{`${task.title}\n日期: ${task.startDate || "未安排"}\n${task.estimatedMinutes}分钟\n${task.done ? "已完成" : "未完成"}${task.note ? "\n" + task.note : ""}`}</title>
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      {tasks.some((t) => t.dependsOn.length > 0) && (
        <p className="text-xs text-slate-500 mt-2">虚线 = dependsOn 依赖关系。节点无坐标时自动按日期排列。</p>
      )}
    </div>
  );
}
