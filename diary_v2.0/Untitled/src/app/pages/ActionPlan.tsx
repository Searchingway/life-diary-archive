import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { Search, Plus, Brain, Sparkles, Calendar, Network } from "lucide-react";

export function ActionPlan() {
  const [selectedPlan, setSelectedPlan] = useState<number | null>(1);
  const [view, setView] = useState<"timetable" | "chain">("timetable");

  const plans = [
    { id: 1, title: "学习前端进阶技能", progress: 65, total: 8, completed: 5, status: "active" },
    { id: 2, title: "建立晨间习惯", progress: 40, total: 10, completed: 4, status: "active" },
  ];

  const tasks = [
    { id: 1, planId: 1, date: "2026-05-28", title: "复习 React 高级特性", time: "2h", status: "pending", isToday: true },
    { id: 2, planId: 1, date: "2026-05-28", title: "整理上周学习笔记", time: "1h", status: "pending", isToday: true },
    { id: 3, planId: 1, date: "2026-05-27", title: "学习 TypeScript 泛型", time: "2h", status: "completed", isToday: false },
    { id: 4, planId: 1, date: "2026-05-26", title: "完成项目实战练习", time: "3h", status: "completed", isToday: false },
    { id: 5, planId: 1, date: "2026-05-29", title: "学习性能优化技巧", time: "2h", status: "pending", isToday: false },
  ];

  const currentPlan = plans.find(p => p.id === selectedPlan);
  const planTasks = tasks.filter(t => t.planId === selectedPlan);

  // Group tasks by date
  const tasksByDate = planTasks.reduce((acc, task) => {
    if (!acc[task.date]) acc[task.date] = [];
    acc[task.date].push(task);
    return acc;
  }, {} as Record<string, typeof tasks>);

  return (
    <div className="h-full flex">
      {/* Left Sidebar - Plan List */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">行动计划</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索计划..." className="pl-9" />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {plans.map((plan) => (
            <button
              key={plan.id}
              onClick={() => setSelectedPlan(plan.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedPlan === plan.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Brain className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{plan.title}</p>
                  <div className="mt-2">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="flex-1 bg-secondary rounded-full h-1.5">
                        <div
                          className="bg-green-500 h-1.5 rounded-full"
                          style={{ width: `${plan.progress}%` }}
                        />
                      </div>
                      <span className="text-xs">{plan.progress}%</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {plan.completed}/{plan.total} 任务完成
                    </p>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {selectedPlan && currentPlan ? (
          <>
            {/* Header */}
            <div className="border-b p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-2xl font-semibold">{currentPlan.title}</h1>
                  <p className="text-muted-foreground mt-1">2026-05-01 至 2026-07-31</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline">
                    <Sparkles className="size-4" />
                    AI 拆解
                  </Button>
                  <Button variant="outline">编辑计划</Button>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: `${currentPlan.progress}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">{currentPlan.progress}%</span>
                </div>
                <span className="text-sm text-muted-foreground">
                  {currentPlan.completed}/{currentPlan.total} 任务完成
                </span>
              </div>
            </div>

            {/* View Tabs */}
            <Tabs value={view} onValueChange={(v) => setView(v as "timetable" | "chain")} className="flex-1 flex flex-col">
              <div className="border-b px-6">
                <TabsList>
                  <TabsTrigger value="timetable">
                    <Calendar className="size-4" />
                    时间表视图
                  </TabsTrigger>
                  <TabsTrigger value="chain">
                    <Network className="size-4" />
                    任务链视图
                  </TabsTrigger>
                </TabsList>
              </div>

              {/* Timetable View */}
              <TabsContent value="timetable" className="flex-1 overflow-y-auto p-6 mt-0">
                <div className="space-y-6 max-w-4xl">
                  {Object.entries(tasksByDate).sort((a, b) => b[0].localeCompare(a[0])).map(([date, dateTasks]) => {
                    const isToday = dateTasks.some(t => t.isToday);
                    return (
                      <div key={date}>
                        <div className={`flex items-center gap-3 mb-3 ${isToday ? "text-primary" : ""}`}>
                          <h3 className="font-semibold">{date}</h3>
                          {isToday && <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">今天</span>}
                        </div>
                        <div className="space-y-3">
                          {dateTasks.map((task) => (
                            <Card key={task.id} className={task.status === "completed" ? "opacity-60" : ""}>
                              <CardContent className="pt-6">
                                <div className="flex items-start gap-3">
                                  <input
                                    type="checkbox"
                                    checked={task.status === "completed"}
                                    className="mt-1"
                                  />
                                  <div className="flex-1">
                                    <p className={`font-medium ${task.status === "completed" ? "line-through" : ""}`}>
                                      {task.title}
                                    </p>
                                    <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                                      <span>预计 {task.time}</span>
                                      {task.status === "completed" && (
                                        <span className="text-green-600">已完成</span>
                                      )}
                                    </div>
                                  </div>
                                  <Button variant="ghost" size="sm">编辑</Button>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                  <Button variant="outline" className="w-full">
                    <Plus className="size-4" />
                    添加任务
                  </Button>
                </div>
              </TabsContent>

              {/* Task Chain View */}
              <TabsContent value="chain" className="flex-1 overflow-y-auto p-6 mt-0">
                <div className="bg-slate-900 rounded-lg p-8 min-h-[600px]">
                  <div className="flex justify-center gap-12">
                    {Object.entries(tasksByDate).sort((a, b) => a[0].localeCompare(b[0])).map(([date, dateTasks]) => (
                      <div key={date} className="flex flex-col items-center">
                        <div className="text-white text-sm mb-4">{date.slice(5)}</div>
                        <div className="flex flex-col items-center gap-4">
                          {dateTasks.map((task, idx) => (
                            <div key={task.id} className="flex flex-col items-center">
                              <div
                                className={`size-16 rounded-full border-4 flex items-center justify-center cursor-pointer transition-all ${
                                  task.status === "completed"
                                    ? "bg-green-500 border-green-400 shadow-lg shadow-green-500/50"
                                    : task.isToday
                                    ? "bg-blue-500 border-blue-400 shadow-lg shadow-blue-500/50"
                                    : "bg-slate-700 border-slate-600"
                                }`}
                              >
                                {task.status === "completed" ? (
                                  <svg className="size-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                ) : (
                                  <span className="text-white font-bold">{idx + 1}</span>
                                )}
                              </div>
                              {idx < dateTasks.length - 1 && (
                                <div className="w-0.5 h-12 bg-slate-600" />
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Brain className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一个计划查看详情</p>
              <p className="text-sm mt-2">或创建新计划</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
