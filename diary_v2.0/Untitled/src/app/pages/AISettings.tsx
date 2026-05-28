import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Settings, Eye, EyeOff, CheckCircle, AlertCircle } from "lucide-react";

export function AISettings() {
  const [aiEnabled, setAiEnabled] = useState(true);
  const [showApiKey, setShowApiKey] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "testing" | "success" | "error">("idle");

  const handleTestConnection = () => {
    setConnectionStatus("testing");
    // Simulate API test
    setTimeout(() => {
      setConnectionStatus("success");
      setTimeout(() => setConnectionStatus("idle"), 3000);
    }, 1500);
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-semibold">AI 设置</h1>
          <p className="text-muted-foreground mt-2">配置 AI 助手功能</p>
        </div>

        {/* Enable AI */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="size-5" />
              启用 AI 功能
            </CardTitle>
            <CardDescription>
              AI 可以帮助你拆解计划、整理思考、评估资源等，但不会直接修改你的数据
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <Label htmlFor="ai-enabled" className="cursor-pointer">
                启用 AI 助手
              </Label>
              <Switch
                id="ai-enabled"
                checked={aiEnabled}
                onCheckedChange={setAiEnabled}
              />
            </div>
          </CardContent>
        </Card>

        {aiEnabled && (
          <>
            {/* API Configuration */}
            <Card>
              <CardHeader>
                <CardTitle>DeepSeek API 配置</CardTitle>
                <CardDescription>
                  配置 DeepSeek API 以使用 AI 功能
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* API Key */}
                <div className="space-y-2">
                  <Label htmlFor="api-key">API Key</Label>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        id="api-key"
                        type={showApiKey ? "text" : "password"}
                        placeholder="sk-..."
                        defaultValue="sk-1234567890abcdef"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showApiKey ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    API Key 将安全地存储在本地，不会上传到任何服务器
                  </p>
                </div>

                {/* Base URL */}
                <div className="space-y-2">
                  <Label htmlFor="base-url">Base URL</Label>
                  <Input
                    id="base-url"
                    placeholder="https://api.deepseek.com"
                    defaultValue="https://api.deepseek.com"
                  />
                </div>

                {/* Model */}
                <div className="space-y-2">
                  <Label htmlFor="model">模型名称</Label>
                  <Input
                    id="model"
                    placeholder="deepseek-chat"
                    defaultValue="deepseek-chat"
                  />
                </div>

                {/* Timeout */}
                <div className="space-y-2">
                  <Label htmlFor="timeout">超时时间（秒）</Label>
                  <Input
                    id="timeout"
                    type="number"
                    placeholder="30"
                    defaultValue="30"
                  />
                </div>

                {/* Test Connection */}
                <div className="pt-4 border-t">
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      onClick={handleTestConnection}
                      disabled={connectionStatus === "testing"}
                    >
                      {connectionStatus === "testing" ? "测试中..." : "测试连接"}
                    </Button>
                    {connectionStatus === "success" && (
                      <div className="flex items-center gap-2 text-green-600">
                        <CheckCircle className="size-4" />
                        <span className="text-sm">连接成功</span>
                      </div>
                    )}
                    {connectionStatus === "error" && (
                      <div className="flex items-center gap-2 text-red-600">
                        <AlertCircle className="size-4" />
                        <span className="text-sm">连接失败，请检查配置</span>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Security Notice */}
            <Card className="border-2 border-orange-500/50">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <AlertCircle className="size-5 text-orange-600 shrink-0 mt-0.5" />
                  <div className="space-y-2">
                    <p className="font-medium text-orange-600">安全提示</p>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• API Key 仅存储在本地设备，不会上传或分享</li>
                      <li>• 日志文件不会记录完整的 API Key</li>
                      <li>• AI 生成的内容需要你确认后才会应用</li>
                      <li>• AI 无法直接访问或修改你的数据</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex justify-end gap-3">
              <Button variant="outline">取消</Button>
              <Button>保存设置</Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
