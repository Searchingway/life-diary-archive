import { useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Activity, AlertTriangle, Database, FileCheck, FolderOpen } from "lucide-react";
import { Overview, getOverview, openDataRoot } from "../lib/api";

export function DataManagement() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [message, setMessage] = useState("正在检查数据");

  useEffect(() => {
    getOverview()
      .then((data) => {
        setOverview(data);
        setMessage(data.migrated_from_legacy ? "首次启动已从旧版目录迁移数据" : "2.0 数据目录可用");
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
  }, []);

  async function handleOpenDataRoot() {
    try {
      await openDataRoot();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "打开数据目录失败");
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-semibold">数据管理</h1>
          <p className="text-muted-foreground mt-2">2.0 使用独立数据目录，首次启动自动从旧版迁移。</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-5" />
              数据位置
            </CardTitle>
            <CardDescription>新版数据与旧版数据分开保存</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">2.0 数据目录</p>
              <div className="p-4 bg-secondary rounded-lg font-mono text-sm break-all">
                {overview?.data_root || "diary_v2.0/data/Diary"}
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-2">旧版来源目录</p>
              <div className="p-4 bg-secondary rounded-lg font-mono text-sm break-all">
                {overview?.legacy_data_root || "data/Diary"}
              </div>
            </div>
            <Button variant="outline" onClick={handleOpenDataRoot}>
              <FolderOpen className="size-4" />
              打开 2.0 数据文件夹
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="size-5" />
              模块数据统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              {(overview?.modules ?? []).map((item) => (
                <div className="p-4 bg-secondary rounded-lg" key={item.key}>
                  <p className="text-sm text-muted-foreground">{item.label}</p>
                  <p className="text-2xl font-bold mt-2">{item.count}</p>
                  <p className="text-xs text-muted-foreground mt-1">{item.latest || "暂无更新"}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCheck className="size-5" />
              数据健康检查
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="flex items-center gap-3">
                <FileCheck className="size-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-600">数据状态正常</p>
                  <p className="text-sm text-muted-foreground mt-1">{message}</p>
                </div>
              </div>
            </div>
            <div className="flex items-start gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
              <AlertTriangle className="size-5 text-orange-600 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-orange-600">迁移说明</p>
                <p className="text-muted-foreground mt-1">
                  2.0 首次启动会复制旧版 data/Diary 到 diary_v2.0/data/Diary。后续保存只写入 2.0 目录，不覆盖旧版。
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
