import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent } from "../components/ui/card";
import { Search, Plus, Lightbulb, Sparkles, Target } from "lucide-react";

export function LightThought() {
  const [selectedThought, setSelectedThought] = useState<number | null>(1);

  const thoughts = [
    { id: 1, title: "如何提高编程效率？", status: "thinking", entryCount: 5 },
    { id: 2, title: "职业发展方向选择", status: "resolved", entryCount: 8 },
  ];

  const entries = [
    { id: 1, date: "2026-05-28", content: "今天尝试了新的时间管理方法，效果不错" },
    { id: 2, date: "2026-05-26", content: "发现问题的关键在于缺乏系统性规划" },
    { id: 3, date: "2026-05-24", content: "阅读了相关文章，获得了一些灵感" },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">轻思考</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索思考..." className="pl-9" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">全部</Button>
            <Button variant="ghost" size="sm" className="flex-1">思考中</Button>
            <Button variant="ghost" size="sm" className="flex-1">已解决</Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {thoughts.map((thought) => (
            <button
              key={thought.id}
              onClick={() => setSelectedThought(thought.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedThought === thought.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Lightbulb className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{thought.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {thought.entryCount} 条思考记录
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedThought ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between">
              <h1 className="text-3xl font-semibold">如何提高编程效率？</h1>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Sparkles className="size-4" />
                  AI 整理
                </Button>
                <Button variant="outline">
                  <Target className="size-4" />
                  转为轻计划
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="pt-6 space-y-4">
                <div>
                  <h3 className="font-medium mb-2">问题描述</h3>
                  <Textarea
                    placeholder="描述这个问题..."
                    className="min-h-[100px]"
                    defaultValue="感觉自己的编程效率不高，经常写着写着就卡住了，不知道如何系统性提升。"
                  />
                </div>
              </CardContent>
            </Card>

            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">思考记录</h3>
                <Button size="sm">
                  <Plus className="size-4" />
                  添加思考
                </Button>
              </div>

              <div className="space-y-4">
                {entries.map((entry) => (
                  <Card key={entry.id}>
                    <CardContent className="pt-6">
                      <p className="text-sm text-muted-foreground mb-2">{entry.date}</p>
                      <p className="text-muted-foreground">{entry.content}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <Card>
              <CardContent className="pt-6 space-y-4">
                <div>
                  <h3 className="font-medium mb-2">当前结论</h3>
                  <Textarea
                    placeholder="当前的结论..."
                    className="min-h-[100px]"
                    defaultValue="需要建立系统的学习方法，同时加强实战练习。"
                  />
                </div>
                <div>
                  <h3 className="font-medium mb-2">下一步行动</h3>
                  <Textarea
                    placeholder="下一步打算做什么..."
                    className="min-h-[80px]"
                    defaultValue="制定详细的学习计划，每天固定时间练习。"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Lightbulb className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一个思考开始记录</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
