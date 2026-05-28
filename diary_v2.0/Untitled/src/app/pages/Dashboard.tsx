import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { PlusCircle, Database, Sparkles, Target, BookOpen, FileText } from "lucide-react";

export function Dashboard() {
  const today = new Date().toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-8 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold">人生档案工作台</h1>
          <p className="text-muted-foreground">{today}</p>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-3">
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2">
                <BookOpen className="size-5" />
                <span className="text-xs">写日记</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2">
                <FileText className="size-5" />
                <span className="text-xs">新信息备忘</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2">
                <Target className="size-5" />
                <span className="text-xs">新轻计划</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2">
                <Sparkles className="size-5" />
                <span className="text-xs">AI 拆解</span>
              </Button>
              <Button variant="outline" className="flex flex-col h-auto py-4 gap-2">
                <Database className="size-5" />
                <span className="text-xs">备份数据</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Two Column Layout */}
        <div className="grid grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Today's Tasks */}
            <Card>
              <CardHeader>
                <CardTitle>今日任务</CardTitle>
                <CardDescription>需要完成的行动计划任务</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 rounded-lg border">
                    <input type="checkbox" className="mt-1" />
                    <div className="flex-1">
                      <p className="font-medium">复习 React 高级特性</p>
                      <p className="text-sm text-muted-foreground">预计 2 小时</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg border">
                    <input type="checkbox" className="mt-1" />
                    <div className="flex-1">
                      <p className="font-medium">整理上周学习笔记</p>
                      <p className="text-sm text-muted-foreground">预计 1 小时</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg border opacity-50">
                    <input type="checkbox" checked className="mt-1" />
                    <div className="flex-1">
                      <p className="font-medium line-through">晨间冥想 20 分钟</p>
                      <p className="text-sm text-muted-foreground">已完成</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* In Progress Action Plans */}
            <Card>
              <CardHeader>
                <CardTitle>进行中的行动计划</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="p-3 rounded-lg border">
                    <p className="font-medium">学习前端进阶技能</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 bg-secondary rounded-full h-2">
                        <div className="bg-primary h-2 rounded-full" style={{ width: "65%" }} />
                      </div>
                      <span className="text-sm text-muted-foreground">65%</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">5/8 任务完成</p>
                  </div>
                  <div className="p-3 rounded-lg border">
                    <p className="font-medium">建立晨间习惯</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 bg-secondary rounded-full h-2">
                        <div className="bg-primary h-2 rounded-full" style={{ width: "40%" }} />
                      </div>
                      <span className="text-sm text-muted-foreground">40%</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">4/10 任务完成</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Recent Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>最近动态</CardTitle>
                <CardDescription>跨模块活动时间线</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-3">
                    <div className="w-1 bg-primary rounded-full" />
                    <div className="flex-1 pb-4">
                      <p className="text-sm text-muted-foreground">今天 14:30</p>
                      <p className="font-medium">写了一篇日记</p>
                      <p className="text-sm text-muted-foreground mt-1">记录了今天的学习心得</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-1 bg-blue-500 rounded-full" />
                    <div className="flex-1 pb-4">
                      <p className="text-sm text-muted-foreground">今天 10:15</p>
                      <p className="font-medium">新增轻思考</p>
                      <p className="text-sm text-muted-foreground mt-1">如何提高编程效率？</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-1 bg-green-500 rounded-full" />
                    <div className="flex-1 pb-4">
                      <p className="text-sm text-muted-foreground">昨天 20:45</p>
                      <p className="font-medium">完成作品感悟</p>
                      <p className="text-sm text-muted-foreground mt-1">《深入理解计算机系统》第三章</p>
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <div className="w-1 bg-orange-500 rounded-full" />
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground">昨天 18:00</p>
                      <p className="font-medium">添加信息备忘</p>
                      <p className="text-sm text-muted-foreground mt-1">新客户项目需求</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <p className="text-sm text-muted-foreground">本月日记</p>
                  <p className="text-3xl font-bold mt-2">18</p>
                  <p className="text-xs text-muted-foreground mt-1">篇</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <p className="text-sm text-muted-foreground">本月字数</p>
                  <p className="text-3xl font-bold mt-2">24.5K</p>
                  <p className="text-xs text-muted-foreground mt-1">字</p>
                </CardContent>
              </Card>
            </div>

            {/* Module Overview */}
            <Card>
              <CardHeader>
                <CardTitle>模块概览</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">日记</span>
                    <span className="font-medium">156</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">足迹</span>
                    <span className="font-medium">42</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">轻计划</span>
                    <span className="font-medium">23</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">行动计划</span>
                    <span className="font-medium">8</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">轻思考</span>
                    <span className="font-medium">31</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">信息备忘</span>
                    <span className="font-medium">67</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
