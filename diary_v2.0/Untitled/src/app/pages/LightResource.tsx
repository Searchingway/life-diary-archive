import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Search, Plus, Scale, Sparkles, Target } from "lucide-react";

export function LightResource() {
  const [selectedResource, setSelectedResource] = useState<number | null>(1);

  const resources = [
    { id: 1, title: "报名线上课程", type: "decision", date: "2026-05-28" },
    { id: 2, title: "接受新项目", type: "opportunity", date: "2026-05-20" },
  ];

  const resourceCategories = [
    { id: "time", label: "时间", value: "每天 2 小时，持续 3 个月" },
    { id: "money", label: "金钱", value: "¥3,999" },
    { id: "energy", label: "精力", value: "需要高度集中，会影响其他事项" },
    { id: "emotion", label: "情绪", value: "学习新东西会有压力，但也有成就感" },
    { id: "courage", label: "勇气", value: "需要走出舒适区" },
    { id: "body", label: "身体", value: "需要调整作息，保证学习时间" },
    { id: "attention", label: "注意力", value: "每天固定时段专注学习" },
    { id: "risk", label: "风险", value: "可能学不完，或者学了用不上" },
    { id: "opportunity", label: "机会成本", value: "这段时间无法做其他事情" },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">轻资源</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索资源评估..." className="pl-9" />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {resources.map((resource) => (
            <button
              key={resource.id}
              onClick={() => setSelectedResource(resource.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedResource === resource.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Scale className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{resource.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{resource.date}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedResource ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-semibold">报名线上课程</h1>
                <p className="text-muted-foreground mt-2">评估这个决定会消耗哪些资源</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Sparkles className="size-4" />
                  AI 评估
                </Button>
                <Button variant="outline">
                  <Target className="size-4" />
                  转为轻计划
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-2">描述</h3>
                <Textarea
                  placeholder="描述这个决定..."
                  className="min-h-[100px]"
                  defaultValue="计划报名一个前端进阶课程，系统学习高级特性和最佳实践。"
                />
              </CardContent>
            </Card>

            <div>
              <h3 className="text-lg font-semibold mb-4">资源消耗评估</h3>
              <div className="grid grid-cols-2 gap-4">
                {resourceCategories.map((category) => (
                  <Card key={category.id}>
                    <CardHeader>
                      <CardTitle className="text-base">{category.label}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{category.value}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <Card className="border-2 border-primary">
              <CardContent className="pt-6 space-y-4">
                <div>
                  <h3 className="font-medium mb-2">永劫回归测试</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    如果这件事重复 10 次，我还会选择吗？
                  </p>
                  <Textarea
                    placeholder="你的思考..."
                    className="min-h-[80px]"
                    defaultValue="如果能真正学到东西，重复 10 次我也愿意。但前提是要确保学习质量，不能浪费时间。"
                  />
                </div>

                <div>
                  <h3 className="font-medium mb-2">综合判断</h3>
                  <Textarea
                    placeholder="最终的判断..."
                    className="min-h-[80px]"
                    defaultValue="值得投入。虽然会消耗较多时间和金钱，但对职业发展有长远帮助。关键是要做好时间规划，确保能坚持学完。"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Scale className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一个资源评估查看详情</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
