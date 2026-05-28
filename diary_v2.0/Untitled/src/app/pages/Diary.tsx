import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card } from "../components/ui/card";
import { Search, Plus, Save, Download, Image as ImageIcon, ChevronDown, ChevronUp } from "lucide-react";

export function Diary() {
  const [selectedDiary, setSelectedDiary] = useState<number | null>(1);
  const [imagesExpanded, setImagesExpanded] = useState(false);

  const diaries = [
    { id: 1, date: "2026-05-28", title: "今天的学习收获", preview: "学习了 React 的高级特性..." },
    { id: 2, date: "2026-05-27", title: "周末思考", preview: "关于未来职业方向的一些想法..." },
    { id: 3, date: "2026-05-26", title: "项目进展", preview: "完成了新功能的开发..." },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar - Diary List */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">日记</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索日记..." className="pl-9" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">
              全部
            </Button>
            <Button variant="ghost" size="sm" className="flex-1">
              本周
            </Button>
            <Button variant="ghost" size="sm" className="flex-1">
              本月
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {diaries.map((diary) => (
            <button
              key={diary.id}
              onClick={() => setSelectedDiary(diary.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedDiary === diary.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <p className="text-xs text-muted-foreground mb-1">{diary.date}</p>
              <p className="font-medium truncate">{diary.title}</p>
              <p className="text-sm text-muted-foreground truncate mt-1">{diary.preview}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {selectedDiary ? (
          <>
            {/* Header */}
            <div className="border-b p-6 space-y-4">
              <div className="flex items-center justify-between">
                <Input
                  placeholder="日记标题"
                  className="text-xl font-semibold border-0 px-0 focus-visible:ring-0"
                  defaultValue="今天的学习收获"
                />
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">已保存</span>
                  <Button variant="outline" size="sm">
                    <Save className="size-4" />
                    保存
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-muted-foreground">2026-05-28 星期三</span>
                <span className="text-muted-foreground">字数: 1,234</span>
              </div>
            </div>

            {/* Writing Area */}
            <div className="flex-1 overflow-y-auto p-6">
              <Textarea
                placeholder="开始写日记..."
                className="min-h-[400px] border-0 resize-none text-base leading-relaxed focus-visible:ring-0"
                defaultValue={`今天深入学习了 React 的高级特性，主要包括 Context API、useMemo、useCallback 等性能优化手段。

通过实际项目练习，我发现性能优化的关键在于找到真正的性能瓶颈，而不是过早优化。很多时候，简单清晰的代码比过度优化的代码更有价值。

另外，我也意识到学习不能只停留在理论层面，必须要通过实际项目来巩固。接下来计划用这些技术重构之前的项目。`}
              />
            </div>

            {/* Secondary Features */}
            <div className="border-t">
              {/* Images Section */}
              <div className="border-b">
                <button
                  onClick={() => setImagesExpanded(!imagesExpanded)}
                  className="w-full px-6 py-3 flex items-center justify-between hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <ImageIcon className="size-4" />
                    <span className="font-medium">图片</span>
                    <span className="text-sm text-muted-foreground">(3)</span>
                  </div>
                  {imagesExpanded ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
                </button>
                {imagesExpanded && (
                  <div className="p-6 grid grid-cols-4 gap-4">
                    <div className="aspect-square rounded-lg bg-secondary border-2 border-dashed flex items-center justify-center cursor-pointer hover:bg-accent transition-colors">
                      <Plus className="size-6 text-muted-foreground" />
                    </div>
                    <div className="aspect-square rounded-lg bg-secondary" />
                    <div className="aspect-square rounded-lg bg-secondary" />
                    <div className="aspect-square rounded-lg bg-secondary" />
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="p-4 flex items-center gap-3">
                <Button variant="outline" size="sm">
                  关联足迹
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="size-4" />
                  导出 Word
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="size-4" />
                  导出 PDF
                </Button>
                <div className="flex-1" />
                <Button variant="ghost" size="sm">
                  查看热力图
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p>选择一篇日记开始编辑</p>
              <p className="text-sm mt-2">或创建新日记</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
