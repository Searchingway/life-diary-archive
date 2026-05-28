import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent } from "../components/ui/card";
import { Search, Plus, User, BookOpen, AlertTriangle, Image as ImageIcon } from "lucide-react";

export function SelfAnalysis() {
  const [selectedAnalysis, setSelectedAnalysis] = useState<number | null>(1);

  const analyses = [
    { id: 1, title: "对失败的过度恐惧", type: "emotion", date: "2026-05-25" },
    { id: 2, title: "重复的拖延模式", type: "pattern", date: "2026-05-18" },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">自我分析</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索分析..." className="pl-9" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">全部</Button>
            <Button variant="ghost" size="sm" className="flex-1">情绪</Button>
            <Button variant="ghost" size="sm" className="flex-1">模式</Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {analyses.map((analysis) => (
            <button
              key={analysis.id}
              onClick={() => setSelectedAnalysis(analysis.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedAnalysis === analysis.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <User className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{analysis.title}</p>
                  <p className="text-xs text-muted-foreground mt-1 capitalize">{analysis.type}</p>
                  <p className="text-xs text-muted-foreground mt-1">{analysis.date}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedAnalysis ? (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-semibold">对失败的过度恐惧</h1>
                <div className="flex items-center gap-3 mt-3">
                  <span className="text-sm px-3 py-1 rounded bg-purple-500/20 text-purple-600">
                    情绪分析
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <BookOpen className="size-4" />
                  关联日记
                </Button>
                <Button variant="outline">
                  <AlertTriangle className="size-4" />
                  关联教训
                </Button>
                <Button variant="outline">
                  <ImageIcon className="size-4" />
                  添加图片
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">触发事件</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="客户提出了新需求，但我担心自己做不好，迟迟不敢开始。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">当时的情绪</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="焦虑、恐惧、不安，担心自己搞砸了会被客户差评。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">身体反应</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="胸口发紧，呼吸急促，晚上睡不好觉，一直在想这件事。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">表层想法</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="这个需求太难了，我可能做不好，不如推掉算了。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">真正的恐惧</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="害怕自己不够好，害怕被否定，害怕证明自己确实没有能力。如果失败了，就说明我真的不行。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">真正的渴望</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="想要得到认可，想要证明自己有能力，想要被看见、被肯定。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">重复模式</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="每次遇到有挑战性的事情，第一反应都是逃避，担心做不好。这个模式从学生时代就开始了。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">想象中他人的评价</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="客户会觉得我太菜了，朋友会觉得我不行，家人会失望。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">防御方式</h3>
                <Textarea
                  className="min-h-[100px]"
                  defaultValue="拖延、找借口、降低期待、提前说'我可能做不好'来保护自己。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">相似的过往经历</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="小时候考试考砸了被父母批评，说'你怎么这么笨'。从那以后就特别害怕失败。"
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">我注意到</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="失败并不等于我这个人不好。很多成功人士也经历过失败。我把失败和自我价值绑定得太紧了。"
                />
              </CardContent>
            </Card>

            <Card className="border-2 border-primary">
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">下一步行动</h3>
                <Textarea
                  className="min-h-[120px]"
                  defaultValue="1. 尝试接受失败是学习的一部分\n2. 把大任务拆成小任务，降低恐惧感\n3. 记录每次尝试，无论成功失败\n4. 寻求支持，不要独自面对"
                />
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <User className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一条分析查看详情</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
