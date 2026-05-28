import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent } from "../components/ui/card";
import { Search, Plus, AlertTriangle, BookOpen, Image as ImageIcon } from "lucide-react";

export function LessonsReflection() {
  const [selectedLesson, setSelectedLesson] = useState<number | null>(1);

  const lessons = [
    { id: 1, title: "项目延期的教训", type: "project", severity: "high", date: "2026-05-20" },
    { id: 2, title: "沟通误解导致的问题", type: "communication", severity: "medium", date: "2026-05-15" },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">教训与反思</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索反思..." className="pl-9" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">全部</Button>
            <Button variant="ghost" size="sm" className="flex-1">项目</Button>
            <Button variant="ghost" size="sm" className="flex-1">情绪</Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {lessons.map((lesson) => (
            <button
              key={lesson.id}
              onClick={() => setSelectedLesson(lesson.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedLesson === lesson.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <AlertTriangle className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{lesson.title}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      lesson.severity === "high" ? "bg-red-500/20 text-red-600" : "bg-orange-500/20 text-orange-600"
                    }`}>
                      {lesson.severity === "high" ? "严重" : "中等"}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{lesson.date}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedLesson ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-semibold">项目延期的教训</h1>
                <div className="flex items-center gap-3 mt-3">
                  <span className="text-sm px-3 py-1 rounded bg-red-500/20 text-red-600">
                    严重
                  </span>
                  <span className="text-sm px-3 py-1 rounded bg-blue-500/20 text-blue-600">
                    项目类型
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <BookOpen className="size-4" />
                  关联日记
                </Button>
                <Button variant="outline">
                  <ImageIcon className="size-4" />
                  添加图片
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">发生了什么</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="承接了一个网站项目，预计 30 天完成，但最终用了 50 天。客户很不满意，差点取消合作。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">当时的想法</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="觉得自己能力足够，30 天应该没问题。没有详细拆解任务，也没有留出缓冲时间。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">结果</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="严重延期，客户信任度下降，自己压力巨大，最后阶段几乎每天加班到深夜。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">判断失误</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="1. 低估了项目复杂度\n2. 没有考虑到客户需求变更的可能性\n3. 过于自信，没有做好风险评估"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">真正的问题</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="缺乏项目管理经验，不会做时间规划，也不敢向客户说明实际情况。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">付出的代价</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="客户关系受损，个人信誉降低，身心俱疲，收入也没有增加。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">下次策略</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="1. 详细拆解任务，预留 30% 缓冲时间\n2. 及时与客户沟通进度\n3. 建立风险预警机制\n4. 不要过度承诺"
                />
              </CardContent>
            </Card>

            <Card className="border-2 border-primary">
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">一句话教训</h3>
                <Textarea
                  className="min-h-[80px]"
                  defaultValue="永远不要低估项目的复杂度，宁可多预留时间，也不要过度承诺。"
                />
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <AlertTriangle className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一条反思查看详情</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
