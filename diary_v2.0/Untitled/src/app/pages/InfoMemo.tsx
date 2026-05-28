import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Search, Plus, FileText, ExternalLink, Folder } from "lucide-react";

export function InfoMemo() {
  const [selectedMemo, setSelectedMemo] = useState<number | null>(1);
  const [typeFilter, setTypeFilter] = useState<"all" | "order" | "course" | "general">("all");

  const memos = [
    { id: 1, title: "客户 A 网站项目", type: "order", status: "active" },
    { id: 2, title: "React 进阶课程", type: "course", status: "active" },
    { id: 3, title: "重要联系人", type: "general", status: "active" },
  ];

  const filteredMemos = memos.filter(m => typeFilter === "all" || m.type === typeFilter);

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">信息备忘</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索信息..." className="pl-9" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={typeFilter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setTypeFilter("all")}
            >
              全部
            </Button>
            <Button
              variant={typeFilter === "order" ? "default" : "outline"}
              size="sm"
              onClick={() => setTypeFilter("order")}
            >
              订单
            </Button>
            <Button
              variant={typeFilter === "course" ? "default" : "outline"}
              size="sm"
              onClick={() => setTypeFilter("course")}
            >
              课程
            </Button>
            <Button
              variant={typeFilter === "general" ? "default" : "outline"}
              size="sm"
              onClick={() => setTypeFilter("general")}
            >
              通用
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {filteredMemos.map((memo) => (
            <button
              key={memo.id}
              onClick={() => setSelectedMemo(memo.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedMemo === memo.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <FileText className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{memo.title}</p>
                  <p className="text-xs text-muted-foreground mt-1 capitalize">{memo.type}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedMemo ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between">
              <h1 className="text-3xl font-semibold">客户 A 网站项目</h1>
              <Button variant="outline">编辑</Button>
            </div>

            {/* Basic Information */}
            <Card>
              <CardHeader>
                <CardTitle>基本信息</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground mb-1">类型</p>
                  <p className="font-medium">自由职业订单</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">状态</p>
                  <p className="font-medium">进行中</p>
                </div>
              </CardContent>
            </Card>

            {/* Customer Information */}
            <Card>
              <CardHeader>
                <CardTitle>客户信息</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground mb-1">客户</p>
                  <p className="font-medium">张先生</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">中介</p>
                  <p className="font-medium">无</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">执行人</p>
                  <p className="font-medium">我</p>
                </div>
              </CardContent>
            </Card>

            {/* Money Information */}
            <div className="grid grid-cols-3 gap-4">
              <Card className="border-2">
                <CardContent className="pt-6 text-center">
                  <p className="text-sm text-muted-foreground mb-2">总价</p>
                  <p className="text-3xl font-bold">¥15,000</p>
                </CardContent>
              </Card>
              <Card className="border-2 border-green-500/50">
                <CardContent className="pt-6 text-center">
                  <p className="text-sm text-muted-foreground mb-2">定金</p>
                  <p className="text-3xl font-bold text-green-600">¥7,500</p>
                </CardContent>
              </Card>
              <Card className="border-2 border-orange-500/50">
                <CardContent className="pt-6 text-center">
                  <p className="text-sm text-muted-foreground mb-2">尾款</p>
                  <p className="text-3xl font-bold text-orange-600">¥7,500</p>
                </CardContent>
              </Card>
            </div>

            {/* Time Information */}
            <Card>
              <CardHeader>
                <CardTitle>时间信息</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground mb-1">接单日期</p>
                  <p className="font-medium">2026-05-01</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">截止日期</p>
                  <p className="font-medium">2026-06-30</p>
                </div>
                <div>
                  <p className="text-muted-foreground mb-1">工期</p>
                  <p className="font-medium">60 天</p>
                </div>
              </CardContent>
            </Card>

            {/* Deliverables */}
            <Card>
              <CardHeader>
                <CardTitle>交付物</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>响应式企业官网</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>后台管理系统</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>源代码及部署文档</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            {/* Links and Paths */}
            <Card>
              <CardHeader>
                <CardTitle>链接与路径</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">相关链接</p>
                  <Button variant="outline" size="sm">
                    <ExternalLink className="size-4" />
                    项目需求文档
                  </Button>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-2">本地文件夹</p>
                  <Button variant="outline" size="sm">
                    <Folder className="size-4" />
                    ~/Projects/客户A网站
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Notes */}
            <Card>
              <CardHeader>
                <CardTitle>备注</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  客户要求使用 React + Tailwind CSS 技术栈，需要特别注意移动端适配。
                  每周五需要提交进度报告。
                </p>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <FileText className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一条信息查看详情</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
