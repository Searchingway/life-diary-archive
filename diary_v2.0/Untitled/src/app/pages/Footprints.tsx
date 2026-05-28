import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Search, Plus, MapPin, Calendar, BookOpen } from "lucide-react";

export function Footprints() {
  const [selectedPlace, setSelectedPlace] = useState<number | null>(1);
  const [selectedVisit, setSelectedVisit] = useState<number | null>(null);

  const places = [
    { id: 1, name: "杭州西湖", visitCount: 5, lastVisit: "2026-05-20" },
    { id: 2, name: "北京故宫", visitCount: 2, lastVisit: "2026-04-15" },
    { id: 3, name: "上海外滩", visitCount: 3, lastVisit: "2026-03-10" },
  ];

  const visits = [
    { id: 1, placeId: 1, date: "2026-05-20", reflection: "春天的西湖格外美丽" },
    { id: 2, placeId: 1, date: "2026-03-15", reflection: "和朋友一起散步" },
    { id: 3, placeId: 1, date: "2025-12-01", reflection: "冬日的西湖别有韵味" },
  ];

  const currentPlace = places.find(p => p.id === selectedPlace);
  const placeVisits = visits.filter(v => v.placeId === selectedPlace);

  return (
    <div className="h-full flex">
      {/* Left Sidebar - Place List */}
      <div className="w-80 border-r bg-card flex flex-col">
        <div className="p-4 border-b space-y-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold flex-1">足迹</h2>
            <Button size="sm">
              <Plus className="size-4" />
              新地点
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
            <Input placeholder="搜索地点..." className="pl-9" />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {places.map((place) => (
            <button
              key={place.id}
              onClick={() => {
                setSelectedPlace(place.id);
                setSelectedVisit(null);
              }}
              className={`w-full text-left p-3 rounded-lg mb-2 transition-colors ${
                selectedPlace === place.id
                  ? "bg-primary text-primary-foreground"
                  : "hover:bg-accent"
              }`}
            >
              <div className="flex items-start gap-2">
                <MapPin className="size-4 mt-1 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{place.name}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    访问 {place.visitCount} 次
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    最近: {place.lastVisit}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        {selectedPlace ? (
          <div className="p-8 space-y-6">
            {/* Place Archive */}
            <Card>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-2xl">{currentPlace?.name}</CardTitle>
                    <p className="text-muted-foreground mt-2">
                      共访问 {currentPlace?.visitCount} 次
                    </p>
                  </div>
                  <Button variant="outline">编辑地点</Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium mb-2">地点描述</h3>
                    <p className="text-muted-foreground">
                      西湖，位于浙江省杭州市西湖区龙井路1号，是中国大陆首批国家重点风景名胜区和中国十大风景名胜之一。
                    </p>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="aspect-video rounded-lg bg-secondary" />
                    <div className="aspect-video rounded-lg bg-secondary" />
                    <div className="aspect-video rounded-lg bg-secondary" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Visit Timeline */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">访问记录</h3>
                <Button size="sm">
                  <Plus className="size-4" />
                  新访问
                </Button>
              </div>

              <div className="space-y-3">
                {placeVisits.map((visit) => (
                  <Card
                    key={visit.id}
                    className={`cursor-pointer transition-colors ${
                      selectedVisit === visit.id ? "border-primary" : "hover:border-primary/50"
                    }`}
                    onClick={() => setSelectedVisit(visit.id)}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-4">
                        <div className="flex flex-col items-center gap-1">
                          <Calendar className="size-5 text-primary" />
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {visit.date}
                          </span>
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium mb-2">访问感想</h4>
                          <p className="text-muted-foreground">{visit.reflection}</p>
                          <div className="mt-4 flex gap-2">
                            <Button variant="outline" size="sm">
                              <BookOpen className="size-4" />
                              打开当日日记
                            </Button>
                            <Button variant="ghost" size="sm">
                              查看图片
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <MapPin className="size-12 mx-auto mb-4 opacity-50" />
              <p>选择一个地点查看访问记录</p>
              <p className="text-sm mt-2">或创建新地点</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
