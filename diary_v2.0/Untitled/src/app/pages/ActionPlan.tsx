import { useEffect, useMemo, useState } from "react";
import { Brain, Calendar, CheckCircle, Plus, Search, Trash2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { RecordItem, listRecords, saveRecord } from "../lib/api";

interface Task {
  id: string;
  title: string;
  date: string;
  time?: string;
  estimated_minutes?: number;
  done?: boolean;
  note?: string;
}

function newPlan(): RecordItem {
  return {
    id: "",
    title: "",
    subtitle: "新行动计划",
    body: "",
    date: new Date().toISOString().slice(0, 10),
    updated_at: "",
    type: "普通行动计划",
    status: "进行中",
    extra: { plan_type: "普通行动计划", tasks: [] },
  };
}

function cnDate(value: string) {
  if (!value) return "未设置日期";
  const [year, month, day] = value.slice(0, 10).split("-");
  return `${year}年${month}月${day}日`;
}

export function ActionPlan() {
  const [plans, setPlans] = useState<RecordItem[]>([]);
  const [selected, setSelected] = useState<RecordItem | null>(null);
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("正在读取行动计划");

  const tasks: Task[] = useMemo(() => (Array.isArray(selected?.extra?.tasks) ? (selected?.extra?.tasks as unknown as Task[]) : []), [selected]);
  const completed = tasks.filter((task) => task.done).length;
  const progress = tasks.length ? Math.round((completed / tasks.length) * 100) : 0;
  const grouped = tasks.reduce<Record<string, Task[]>>((result, task) => {
    const key = task.date || selected?.date || "未设置日期";
    result[key] = [...(result[key] ?? []), task];
    return result;
  }, {});

  async function load(keyword = query) {
    const data = await listRecords("action_plans", keyword);
    setPlans(data);
    setSelected((current) => (current?.id ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null));
  }

  useEffect(() => {
    load("").catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  function patch(patchValue: Partial<RecordItem>) {
    setSelected((current) => (current ? { ...current, ...patchValue } : current));
  }

  function patchTasks(nextTasks: Task[]) {
    if (!selected) return;
    patch({ extra: { ...(selected.extra ?? {}), tasks: nextTasks } });
  }

  async function saveSelected() {
    if (!selected) return;
    const saved = await saveRecord("action_plans", selected);
    setSelected(saved);
    setPlans((items) => (items.some((item) => item.id === saved.id) ? items.map((item) => (item.id === saved.id ? saved : item)) : [saved, ...items]));
    setMessage(`已保存 ${new Date().toLocaleTimeString()}`);
  }

  function addTask() {
    patchTasks([
      ...tasks,
      {
        id: crypto.randomUUID(),
        title: "新子任务",
        date: selected?.date || new Date().toISOString().slice(0, 10),
        time: "",
        done: false,
        note: "",
      },
    ]);
  }

  function updateTask(taskId: string, patchValue: Partial<Task>) {
    patchTasks(tasks.map((task) => (task.id === taskId ? { ...task, ...patchValue } : task)));
  }

  function removeTask(taskId: string) {
    patchTasks(tasks.filter((task) => task.id !== taskId));
  }

  return (
    <div className="h-full flex">
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">行动计划</h2>
            <Button size="sm" onClick={() => setSelected(newPlan())}>
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
          <p className="text-xs text-muted-foreground">{message}</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {plans.map((plan) => {
            const planTasks = Array.isArray(plan.extra?.tasks) ? plan.extra.tasks : [];
            const done = planTasks.filter((task) => typeof task === "object" && task && (task as Task).done).length;
            const percent = planTasks.length ? Math.round((done / planTasks.length) * 100) : 0;
            return (
              <button
                key={plan.id}
                onClick={() => setSelected(plan)}
                className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                  selected?.id === plan.id ? "bg-primary text-primary-foreground" : "hover:bg-accent"
                }`}
              >
                <div className="flex items-start gap-2">
                  <Brain className="size-4 mt-1 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{plan.title || "未命名行动计划"}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 bg-secondary rounded-full h-1.5">
                        <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${percent}%` }} />
                      </div>
                      <span className="text-xs">{percent}%</span>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        {selected ? (
          <>
            <div className="border-b p-6 space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-3 flex-1">
                  <Input
                    className="text-2xl font-semibold border-0 px-0 focus-visible:ring-0"
                    value={selected.title}
                    placeholder="行动计划标题"
                    onChange={(event) => patch({ title: event.target.value })}
                  />
                  <div className="flex items-center gap-3">
                    <select
                      className="h-9 rounded-md border bg-background px-3 text-sm"
                      value={String(selected.extra?.plan_type || selected.type || "普通行动计划")}
                      onChange={(event) => patch({ type: event.target.value, extra: { ...(selected.extra ?? {}), plan_type: event.target.value, tasks } })}
                    >
                      <option value="普通行动计划">普通行动计划</option>
                      <option value="日程型行动计划">日程型行动计划</option>
                    </select>
                    <Input className="w-40" value={selected.date || ""} onChange={(event) => patch({ date: event.target.value })} />
                    <span className="text-sm text-muted-foreground">{completed}/{tasks.length} 子任务完成</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={addTask}>
                    <Plus className="size-4" />
                    子任务
                  </Button>
                  <Button onClick={saveSelected}>保存</Button>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-44 bg-secondary rounded-full h-2">
                  <div className="bg-primary h-2 rounded-full" style={{ width: `${progress}%` }} />
                </div>
                <span className="text-sm font-medium">{progress}%</span>
              </div>
              <Textarea className="min-h-[90px]" value={selected.body || ""} onChange={(event) => patch({ body: event.target.value })} placeholder="计划说明" />
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {Object.entries(grouped)
                .sort((a, b) => b[0].localeCompare(a[0]))
                .map(([date, dateTasks]) => (
                  <div key={date}>
                    <div className="flex items-center gap-3 mb-3 text-primary">
                      <Calendar className="size-5" />
                      <h3 className="font-semibold">{cnDate(date)}</h3>
                    </div>
                    <div className="space-y-3">
                      {dateTasks.map((task) => (
                        <Card key={task.id} className={task.done ? "opacity-70" : ""}>
                          <CardContent className="pt-5">
                            <div className="grid grid-cols-[auto_1fr_130px_100px_auto] gap-3 items-start">
                              <input
                                type="checkbox"
                                className="mt-3"
                                checked={Boolean(task.done)}
                                onChange={(event) => updateTask(task.id, { done: event.target.checked })}
                              />
                              <div className="space-y-2">
                                <Input
                                  value={task.title}
                                  onChange={(event) => updateTask(task.id, { title: event.target.value })}
                                  className={task.done ? "line-through" : ""}
                                />
                                <Input value={task.note || ""} onChange={(event) => updateTask(task.id, { note: event.target.value })} placeholder="备注" />
                              </div>
                              <Input value={task.date} onChange={(event) => updateTask(task.id, { date: event.target.value })} />
                              <Input value={task.time || ""} onChange={(event) => updateTask(task.id, { time: event.target.value })} placeholder="时间" />
                              <Button variant="ghost" size="sm" onClick={() => removeTask(task.id)}>
                                <Trash2 className="size-4" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                ))}
              {tasks.length === 0 && (
                <div className="text-center text-muted-foreground py-12">
                  <CheckCircle className="size-10 mx-auto mb-3 opacity-50" />
                  还没有子任务
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="h-full grid place-content-center text-muted-foreground">选择一个行动计划查看详情</div>
        )}
      </div>
    </div>
  );
}
