import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Database, Download, Upload, FolderOpen, FileCheck, AlertTriangle, Activity } from "lucide-react";

export function DataManagement() {
  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-semibold">数据管理</h1>
          <p className="text-muted-foreground mt-2">本地数据备份、恢复与导入导出</p>
        </div>

        {/* Data Location */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-5" />
              数据位置
            </CardTitle>
            <CardDescription>本地数据存储路径</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 bg-secondary rounded-lg font-mono text-sm">
              ~/Library/Application Support/PersonalArchive/data/
            </div>
            <div className="mt-4">
              <Button variant="outline">
                <FolderOpen className="size-4" />
                打开数据文件夹
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Backup */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="size-5" />
              备份
            </CardTitle>
            <CardDescription>创建数据备份副本</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-secondary rounded-lg">
              <div>
                <p className="font-medium">上次备份</p>
                <p className="text-sm text-muted-foreground mt-1">2026-05-27 20:30</p>
              </div>
              <Button>
                <Download className="size-4" />
                立即备份
              </Button>
            </div>
            <div className="text-sm text-muted-foreground">
              <p>备份将包含所有日记、足迹、计划、思考等数据。</p>
              <p className="mt-1">建议定期备份以防数据丢失。</p>
            </div>
          </CardContent>
        </Card>

        {/* Restore */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="size-5" />
              恢复
            </CardTitle>
            <CardDescription>从备份文件恢复数据</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 border-2 border-dashed rounded-lg text-center">
              <Upload className="size-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground mb-3">选择备份文件恢复</p>
              <Button variant="outline">选择备份文件</Button>
            </div>
            <div className="flex items-start gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
              <AlertTriangle className="size-5 text-orange-600 shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-orange-600">警告</p>
                <p className="text-muted-foreground mt-1">
                  恢复操作会覆盖当前数据。建议先备份当前数据再执行恢复操作。
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Import Mobile */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="size-5" />
              导入移动端数据
            </CardTitle>
            <CardDescription>从移动端导出的 ZIP 文件导入数据</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 border-2 border-dashed rounded-lg text-center">
              <Upload className="size-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground mb-3">选择移动端导出的 ZIP 文件</p>
              <Button variant="outline">选择 ZIP 文件</Button>
            </div>
            <div className="text-sm space-y-2">
              <p className="font-medium">导入说明：</p>
              <ul className="list-disc list-inside text-muted-foreground space-y-1">
                <li>系统会自动读取 ZIP 文件中的 manifest.json</li>
                <li>导入前会自动备份当前桌面端数据</li>
                <li>数据会根据 ID 进行合并，不会覆盖整个数据集</li>
                <li>重复的 ID 会保留桌面端数据</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Export Desktop */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="size-5" />
              导出桌面端数据
            </CardTitle>
            <CardDescription>导出数据为 ZIP 文件</CardDescription>
          </CardHeader>
          <CardContent>
            <Button>
              <Download className="size-4" />
              导出 ZIP
            </Button>
          </CardContent>
        </Card>

        {/* Statistics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="size-5" />
              模块数据统计
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 bg-secondary rounded-lg">
                <p className="text-sm text-muted-foreground">日记</p>
                <p className="text-2xl font-bold mt-2">156</p>
              </div>
              <div className="p-4 bg-secondary rounded-lg">
                <p className="text-sm text-muted-foreground">足迹</p>
                <p className="text-2xl font-bold mt-2">42</p>
              </div>
              <div className="p-4 bg-secondary rounded-lg">
                <p className="text-sm text-muted-foreground">轻计划</p>
                <p className="text-2xl font-bold mt-2">23</p>
              </div>
              <div className="p-4 bg-secondary rounded-lg">
                <p className="text-sm text-muted-foreground">行动计划</p>
                <p className="text-2xl font-bold mt-2">8</p>
              </div>
              <div className="p-4 bg-secondary rounded-lg">
                <p className="text-sm text-muted-foreground">轻思考</p>
                <p className="text-2xl font-bold mt-2">31</p>
              </div>
              <div className="p-4 bg-secondary rounded-lg">
                <p className="text-sm text-muted-foreground">信息备忘</p>
                <p className="text-2xl font-bold mt-2">67</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Health Check */}
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
                  <p className="text-sm text-muted-foreground mt-1">最后检查: 2026-05-28 09:00</p>
                </div>
              </div>
              <Button variant="outline">重新检查</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
