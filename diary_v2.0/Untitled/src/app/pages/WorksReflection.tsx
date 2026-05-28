import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent } from "../components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "../components/ui/collapsible";
import { Search, Plus, Film, ChevronDown, BookOpen, User } from "lucide-react";

export function WorksReflection() {
  const [selectedWork, setSelectedWork] = useState<number | null>(1);
  const [quotesExpanded, setQuotesExpanded] = useState(false);

  const works = [
    { id: 1, title: "深入理解计算机系统", type: "book", status: "completed", rating: 5 },
    { id: 2, title: "黑客帝国", type: "film", status: "completed", rating: 5 },
    { id: 3, title: "React 官方教程", type: "course", status: "in-progress", rating: null },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">作品感悟</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索作品..." className="pl-9" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" size="sm">全部</Button>
            <Button variant="ghost" size="sm">书籍</Button>
            <Button variant="ghost" size="sm">影视</Button>
            <Button variant="ghost" size="sm">课程</Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {works.map((work) => (
            <button
              key={work.id}
              onClick={() => setSelectedWork(work.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedWork === work.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Film className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{work.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs capitalize">{work.type}</span>
                    {work.rating && (
                      <span className="text-xs">{"⭐".repeat(work.rating)}</span>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedWork ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-semibold">深入理解计算机系统</h1>
                <div className="flex items-center gap-3 mt-3">
                  <span className="text-sm px-3 py-1 rounded bg-blue-500/20 text-blue-600">
                    书籍
                  </span>
                  <span className="text-sm px-3 py-1 rounded bg-green-500/20 text-green-600">
                    已完成
                  </span>
                  <span className="text-xl">⭐⭐⭐⭐⭐</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <BookOpen className="size-4" />
                  关联日记
                </Button>
                <Button variant="outline">
                  <User className="size-4" />
                  关联自我分析
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-2">作者</h3>
                  <p className="text-muted-foreground">Randal E. Bryant, David R. O'Hallaron</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-2">状态</h3>
                  <p className="text-muted-foreground">已读完</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-2">开始日期</h3>
                  <p className="text-muted-foreground">2026-03-01</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-2">完成日期</h3>
                  <p className="text-muted-foreground">2026-05-20</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-2">标签</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  <span className="text-xs px-2 py-1 rounded bg-secondary">计算机科学</span>
                  <span className="text-xs px-2 py-1 rounded bg-secondary">系统编程</span>
                  <span className="text-xs px-2 py-1 rounded bg-secondary">底层原理</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardContent className="pt-6">
                <h3 className="text-lg font-medium mb-4">我的感悟</h3>
                <Textarea
                  className="min-h-[300px] text-base leading-relaxed"
                  defaultValue={`这本书彻底改变了我对计算机的理解。以前只会用高级语言写代码，对底层完全不了解。读完这本书后，终于明白了程序是如何在计算机上运行的。

最大的收获：
1. 理解了内存层次结构，知道为什么某些代码跑得快，某些跑得慢
2. 学会了用系统的视角看问题，而不只是停留在语言特性上
3. 对并发、网络编程有了更深的理解

这本书很厚，读起来确实费劲，但每一章都值得反复琢磨。强烈推荐给想要深入理解计算机的人。

读这本书的过程也是一个自我挑战，有很多次想放弃，但坚持下来后发现自己的技术视野真的开阔了很多。`}
                />
              </CardContent>
            </Card>

            <Collapsible open={quotesExpanded} onOpenChange={setQuotesExpanded}>
              <Card>
                <CollapsibleTrigger className="w-full">
                  <CardContent className="pt-6 pb-6">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium">摘抄与笔记</h3>
                      <ChevronDown className={`size-4 transition-transform ${quotesExpanded ? "rotate-180" : ""}`} />
                    </div>
                  </CardContent>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <CardContent className="pt-0">
                    <div className="space-y-4 border-t pt-4">
                      <div className="pl-4 border-l-2 border-primary">
                        <p className="text-muted-foreground italic mb-2">
                          "理解计算机系统的工作原理，是成为优秀程序员的基础。"
                        </p>
                        <p className="text-xs text-muted-foreground">第 1 章</p>
                      </div>
                      <div className="pl-4 border-l-2 border-primary">
                        <p className="text-muted-foreground italic mb-2">
                          "程序的性能不仅取决于算法，还取决于你如何利用底层系统。"
                        </p>
                        <p className="text-xs text-muted-foreground">第 6 章</p>
                      </div>
                    </div>
                  </CardContent>
                </CollapsibleContent>
              </Card>
            </Collapsible>

            <div className="grid grid-cols-3 gap-4">
              <div className="aspect-[2/3] rounded-lg bg-secondary" />
              <div className="aspect-[2/3] rounded-lg bg-secondary" />
              <div className="aspect-[2/3] rounded-lg bg-secondary" />
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Film className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一个作品查看感悟</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
