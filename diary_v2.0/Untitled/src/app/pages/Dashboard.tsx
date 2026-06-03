import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { BookOpen, Database, FileText, PlusCircle, Sparkles, Target } from "lucide-react";
import { Overview, getOverview } from "../lib/api";

export function Dashboard() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [message, setMessage] = useState("正在读取 2.0 数据");

  const today = new Date().toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  useEffect(() => {
    getOverview()
      .then((data) => {
        setOverview(data);
        setMessage(data.migrated_from_legacy ? "已从旧版数据迁移到 2.0" : "正在使用 2.0 本地数据");
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  const moduleCount = overview?.modules.reduce((sum, item) => sum + item.count, 0) ?? 0;
  const stats = overview?.modules ?? [];
  const dashboardStats = overview?.dashboard_stats;
  const basicStats = [
    { label: "本月日记篇数", value: dashboardStats?.month_diary_count ?? 0 },
    { label: "本月日记总字数", value: dashboardStats?.month_diary_words ?? 0 },
    { label: "本月日记图片数", value: dashboardStats?.month_diary_images ?? 0 },
    { label: "本月完成计划数", value: dashboardStats?.month_completed_plans ?? 0 },
    { label: "今年日记篇数", value: dashboardStats?.year_diary_count ?? 0 },
    { label: "今年日记总字数", value: dashboardStats?.year_diary_words ?? 0 },
    { label: "今年日记图片数", value: dashboardStats?.year_diary_images ?? 0 },
    { label: "今年完成计划数", value: dashboardStats?.year_completed_plans ?? 0 },
    { label: "行动计划总数", value: dashboardStats?.action_plan_count ?? 0 },
    { label: "进行中", value: dashboardStats?.active_action_plan_count ?? 0 },
    { label: "今日待办任务", value: dashboardStats?.today_pending_tasks ?? 0 },
  ];

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold">人生档案工作台</h1>
          <p className="text-muted-foreground">{today}</p>
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-3">
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2" onClick={() => navigate("/diary?new=1")}>
                <BookOpen className="size-5" />
                <span className="text-xs">写日记</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2" onClick={() => navigate("/info-memo?new=1")}>
                <FileText className="size-5" />
                <span className="text-xs">新信息备忘</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2" onClick={() => navigate("/light-plan?new=1")}>
                <Target className="size-5" />
                <span className="text-xs">新轻计划</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2" onClick={() => navigate("/action-plan?new=1&type=schedule")}>
                <Sparkles className="size-5" />
                <span className="text-xs">AI 拆解</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2" onClick={() => navigate("/data-management")}>
                <Database className="size-5" />
                <span className="text-xs">数据管理</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>基础统计</CardTitle>
            <CardDescription>日记、图片、计划和今日任务的真实数据</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-3">
              {basicStats.map((item) => (
                <div key={item.label} className="bg-secondary/60 rounded-lg p-4">
                  <p className="text-sm">{item.label}</p>
                  <p className="text-3xl font-bold mt-2 text-primary">{item.value}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>最近动态</CardTitle>
              <CardDescription>从旧版数据迁移后的真实时间线</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(overview?.recent ?? []).slice(0, 8).map((item) => (
                  <div className="flex gap-3" key={`${item.module_key}-${item.id}`}>
                    <div className="w-1 bg-primary rounded-full" />
                    <div className="flex-1 pb-2">
                      <p className="text-sm text-muted-foreground">{item.date || item.updated_at?.slice(0, 10)}</p>
                      <p className="font-medium">{item.title || "未命名记录"}</p>
                      <p className="text-sm text-muted-foreground mt-1">{item.module}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>模块概览</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 text-sm">
                {stats.map((item) => (
                  <div className="flex justify-between" key={item.key}>
                    <span className="text-muted-foreground">{item.label}</span>
                    <span className="font-medium">{item.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">2.0 本地记录</p>
              <p className="text-3xl font-bold mt-2">{moduleCount}</p>
              <p className="text-xs text-muted-foreground mt-1">条</p>
            </CardContent>
          </Card>
          <Card className="col-span-2">
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground">数据目录</p>
              <p className="font-mono text-sm mt-2 break-all">{overview?.data_root || "diary_v2.0/data/Diary"}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
