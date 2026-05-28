import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent } from "../components/ui/card";
import { Search, Plus, Eye } from "lucide-react";

export function SelfObservation() {
  const [selectedObs, setSelectedObs] = useState<number | null>(1);

  const observations = [
    { id: 1, date: "2026-05-28 14:30", emotion: "焦虑", intensity: "中等" },
    { id: 2, date: "2026-05-28 09:15", emotion: "平静", intensity: "轻微" },
    { id: 3, date: "2026-05-27 20:00", emotion: "疲惫", intensity: "强烈" },
  ];

  return (
    <div className="h-full flex">
      {/* Left Sidebar */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">自我观察</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新建
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索观察..." className="pl-9" />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">全部</Button>
            <Button variant="ghost" size="sm" className="flex-1">本周</Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {observations.map((obs) => (
            <button
              key={obs.id}
              onClick={() => setSelectedObs(obs.id)}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedObs === obs.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <Eye className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium">{obs.emotion}</p>
                  <p className="text-xs text-muted-foreground mt-1">{obs.date}</p>
                  <p className="text-xs text-muted-foreground mt-1">强度: {obs.intensity}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {selectedObs ? (
          <div className="max-w-3xl space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-3xl font-semibold">自我观察记录</h1>
                <p className="text-muted-foreground mt-2">2026-05-28 14:30</p>
              </div>
              <Button variant="outline">转为自我分析</Button>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-3">情绪</h3>
                  <p className="text-2xl font-semibold">焦虑</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <h3 className="font-medium mb-3">强度</h3>
                  <p className="text-2xl font-semibold">中等</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">当前需求</h3>
                <p className="text-muted-foreground">
                  需要完成项目，但感觉时间不够，想要得到认可
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">触发事件</h3>
                <p className="text-muted-foreground">
                  客户催促项目进度，担心无法按时完成
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">身体感受</h3>
                <p className="text-muted-foreground">
                  胸口发紧，呼吸有点急促，手心出汗
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <h3 className="font-medium mb-3">备注</h3>
                <p className="text-muted-foreground">
                  深呼吸后好了一些，决定先把任务拆解成小块，一步步完成
                </p>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Eye className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一条观察记录查看详情</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
