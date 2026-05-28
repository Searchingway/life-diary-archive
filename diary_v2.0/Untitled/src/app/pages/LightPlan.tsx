import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Search, Plus, Target, CheckCircle, Sparkles, ArrowRight } from "lucide-react";

export function LightPlan() {
  const [selectedPlan, setSelectedPlan] = useState<number | null>(1);
  const [filter, setFilter] = useState<"all" | "additive" | "subtractive" | "completed">("all");

  const plans = [
    { id: 1, title: "每天学习编程 1 小时", type: "additive", status: "active" },
    { id: 2, title: "减少刷短视频时间", type: "subtractive", status: "active" },
    { id: 3, title: "建立晨间冥想习惯", type: "additive", status: "completed" },
  ];

  const filteredPlans = plans.filter(plan => {
    if (filter === "all") return true;
    if (filter === "completed") return plan.status === "completed";
    return plan.type === filter;
  });

  const currentPlan = plans.find(p => p.id === selectedPlan);

  return (
    <div className="h-full flex">
      {/* Left Sidebar - Plan List */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">轻计划</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索计划..." className="pl-9" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={filter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("all")}
            >
              全部
            </Button>
            <Button
              variant={filter === "additive" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("additive")}
            >
              增量
            </Button>
            <Button
              variant={filter === "subtractive" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("subtractive")}
            >
              减量
            </Button>
            <Button
              variant={filter === "completed" ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter("completed")}
            >
              已完成
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {filteredPlans.map((plan) => (
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
                <Target className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{plan.title}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      plan.type === "additive" ? "bg-green-500/20 text-green-600" : "bg-orange-500/20 text-orange-600"
                    }`}>
                      {plan.type === "additive" ? "增量计划" : "减量计划"}
                    </span>
                    {plan.status === "completed" && (
                      <CheckCircle className="size-3 text-green-600" />
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        {selectedPlan && currentPlan ? (
          <div className="p-8 max-w-4xl">
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-3xl font-semibold">{currentPlan.title}</h1>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-sm px-2 py-1 rounded ${
                      currentPlan.type === "additive" ? "bg-green-500/20 text-green-600" : "bg-orange-500/20 text-orange-600"
                    }`}>
                      {currentPlan.type === "additive" ? "增量计划" : "减量计划"}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline">编辑</Button>
                  {currentPlan.status !== "completed" && (
                    <Button>
                      <CheckCircle className="size-4" />
                      标记完成
                    </Button>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <Button variant="outline">
                  <Sparkles className="size-4" />
                  AI 完善计划
                </Button>
                <Button variant="outline">
                  <ArrowRight className="size-4" />
                  转为行动计划
                </Button>
              </div>

              {/* Plan Details */}
              {currentPlan.type === "additive" ? (
                <Card>
                  <CardContent className="pt-6 space-y-6">
                    <div>
                      <h3 className="font-medium mb-2">计划描述</h3>
                      <p className="text-muted-foreground">
                        通过每天固定学习 1 小时编程，系统性提升技术能力，为未来的职业发展打好基础。
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">期望成果</h3>
                      <p className="text-muted-foreground">
                        3 个月后能够独立完成中等复杂度的项目，掌握主流前端框架和最佳实践。
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">具体行动</h3>
                      <ul className="text-muted-foreground space-y-2">
                        <li>• 每天早上 9:00-10:00 固定学习时间</li>
                        <li>• 学习资料：官方文档 + 实战项目</li>
                        <li>• 记录学习笔记和心得</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="pt-6 space-y-6">
                    <div>
                      <h3 className="font-medium mb-2">触发场景</h3>
                      <p className="text-muted-foreground">
                        晚上睡前、吃饭时、无聊时
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">要避免的行为</h3>
                      <p className="text-muted-foreground">
                        刷短视频超过 30 分钟
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">原因</h3>
                      <p className="text-muted-foreground">
                        短视频会消耗大量时间，导致注意力碎片化，影响学习和工作效率
                      </p>
                    </div>
                    <div>
                      <h3 className="font-medium mb-2">替代行为</h3>
                      <p className="text-muted-foreground">
                        看书、听播客、散步、冥想
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Progress Tracking */}
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-4">进度跟踪</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">创建日期</span>
                      <span>2026-05-01</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">已坚持</span>
                      <span className="font-medium">28 天</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Target className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一个计划查看详情</p>
              <p className="text-sm mt-2">或创建新计划</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
