import { useEffect, useRef, useState } from "react";
import { useBlocker } from "react-router";
import { AlertCircle, CheckCircle, Eye, EyeOff, LoaderCircle, Settings } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { AIConfiguration, AIConfigurationDraft, getAIConfiguration, saveAIConfiguration, testAIConfiguration } from "../lib/api";

export function AISettings() {
  const [saved, setSaved] = useState<AIConfiguration | null>(null);
  const [draft, setDraft] = useState<AIConfigurationDraft | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [clearKey, setClearKey] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<"save" | "test" | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const requestId = useRef(0);
  const busyRef = useRef(false);
  const dirty = Boolean(saved && draft && (
    draft.enabled !== saved.enabled || draft.base_url !== saved.base_url || draft.model !== saved.model ||
    draft.timeout_seconds !== saved.timeout_seconds || draft.api_key || clearKey
  ));
  const blocker = useBlocker(dirty || busy === "save");

  function reset(configuration: AIConfiguration) {
    const { has_api_key: _hasKey, ...values } = configuration;
    setSaved(configuration);
    setDraft({ ...values, api_key: "" });
    setClearKey(false);
    setShowKey(false);
  }
  async function load() {
    const current = ++requestId.current;
    setLoading(true);
    setError("");
    try {
      const configuration = await getAIConfiguration();
      if (requestId.current === current) reset(configuration);
    } catch (cause) {
      if (requestId.current === current) setError(cause instanceof Error ? cause.message : "读取失败");
    } finally {
      if (requestId.current === current) setLoading(false);
    }
  }
  useEffect(() => { void load(); return () => { requestId.current += 1; }; }, []);
  useEffect(() => {
    const protect = (event: BeforeUnloadEvent) => {
      if (dirty || busy === "save") { event.preventDefault(); event.returnValue = ""; }
    };
    window.addEventListener("beforeunload", protect);
    return () => window.removeEventListener("beforeunload", protect);
  }, [dirty, busy]);

  function patch(values: Partial<AIConfigurationDraft>) {
    if (busyRef.current) return;
    setDraft(current => current ? { ...current, ...values } : current);
    setMessage("");
    setError("");
  }
  async function perform(action: "save" | "test"): Promise<boolean> {
    if (!draft || busyRef.current) return false;
    busyRef.current = true;
    setBusy(action);
    setError("");
    setMessage("");
    const { api_key, ...values } = draft;
    const payload = { ...values, ...(clearKey ? { api_key: "" } : api_key?.trim() ? { api_key: api_key.trim() } : {}) };
    try {
      if (action === "save") {
        reset(await saveAIConfiguration(payload));
        setMessage("设置已保存到本机");
      } else {
        const result = await testAIConfiguration(payload);
        setMessage(result.message);
      }
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "操作失败，输入仍保留");
      return false;
    } finally {
      busyRef.current = false;
      setBusy(null);
    }
  }

  return <div className="min-h-full bg-secondary/20">
    <div className="mx-auto max-w-3xl space-y-6 p-4 sm:p-8">
      <header><h1 className="text-3xl font-semibold">AI 设置</h1><p className="mt-2 text-sm text-muted-foreground">管理本机的模型连接。测试连接使用当前填写的参数，不会保存配置。</p></header>
      {loading && <p role="status">正在读取本地设置…</p>}
      {error && <div role="alert" className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive"><AlertCircle className="mt-0.5 size-4 shrink-0" /><span>{error}</span>{!draft && <Button variant="outline" size="sm" onClick={() => void load()}>重试</Button>}</div>}
      {message && <p role="status" className="flex items-center gap-2 rounded-lg border bg-card p-4 text-sm"><CheckCircle className="size-4 shrink-0" />{message}</p>}
      {draft && <>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Settings className="size-5" />模型连接</CardTitle><CardDescription>兼容 DeepSeek / OpenAI 格式的 API</CardDescription></CardHeader>
          <CardContent>
            <fieldset disabled={Boolean(busy)} className="space-y-6">
              <div className="flex items-center justify-between gap-4"><Label htmlFor="ai-enabled">启用 AI 助手</Label><Switch id="ai-enabled" checked={draft.enabled} onCheckedChange={enabled => patch({ enabled })} /></div>
              <div className="space-y-2"><Label htmlFor="api-key">API Key</Label>
                <div className="relative"><Input id="api-key" type={showKey ? "text" : "password"} autoComplete="off" spellCheck={false} className="pr-12" value={draft.api_key || ""} placeholder={saved?.has_api_key && !clearKey ? "已保存密钥；留空保留原密钥" : "输入 API Key"} onChange={event => { setClearKey(false); patch({ api_key: event.target.value }); }} />
                  <Button type="button" variant="ghost" size="icon" className="absolute right-0 top-0" aria-label={showKey ? "隐藏密钥" : "显示密钥"} onClick={() => setShowKey(!showKey)}>{showKey ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</Button>
                </div>
                <p className="text-xs text-muted-foreground">{clearKey ? "保存后将清除密钥并关闭 AI。" : saved?.has_api_key ? "已有密钥保存在本机，接口不会返回完整密钥。" : "尚未保存密钥。"}</p>
                {saved?.has_api_key && !clearKey && <Button type="button" variant="link" size="sm" className="px-0 text-destructive" onClick={() => { patch({ api_key: "", enabled: false }); setClearKey(true); }}>清除已保存密钥</Button>}
              </div>
              <div className="space-y-2"><Label htmlFor="base-url">Base URL</Label><Input id="base-url" type="url" value={draft.base_url} onChange={event => patch({ base_url: event.target.value })} /><p className="text-xs text-muted-foreground">更换服务主机时，请重新填写该服务的 API Key。</p></div>
              <div className="grid gap-5 sm:grid-cols-2"><div className="space-y-2"><Label htmlFor="model">模型名称</Label><Input id="model" value={draft.model} onChange={event => patch({ model: event.target.value })} /></div>
                <div className="space-y-2"><Label htmlFor="timeout">超时时间（秒）</Label><Input id="timeout" type="number" min={5} max={180} step={1} value={Number.isFinite(draft.timeout_seconds) ? draft.timeout_seconds : ""} onChange={event => patch({ timeout_seconds: event.target.value === "" ? Number.NaN : Number(event.target.value) })} /></div></div>
              <Button variant="outline" disabled={clearKey} onClick={() => void perform("test")}>{busy === "test" && <LoaderCircle className="size-4 motion-safe:animate-spin" />}{busy === "test" ? "测试中…" : "测试连接"}</Button>
            </fieldset>
          </CardContent>
        </Card>
        <p className="text-xs leading-relaxed text-muted-foreground">配置保存在本地。点击测试会向你填写的服务地址发送连接请求及密钥；不会发送日记内容。AI 生成内容仍须预览并由你确认后应用。</p>
        <div className="flex flex-wrap items-center justify-end gap-3"><span className="mr-auto text-xs text-muted-foreground">{dirty ? "有未保存的设置" : "设置已同步"}</span><Button variant="outline" disabled={Boolean(busy) || !dirty} onClick={() => { if (saved) reset(saved); setMessage("已取消修改"); setError(""); }}>取消修改</Button><Button disabled={Boolean(busy) || !dirty} onClick={() => void perform("save")}>{busy === "save" ? "保存中…" : "保存设置"}</Button></div>
      </>}
      <Dialog open={blocker.state === "blocked"} onOpenChange={open => { if (!open && !busy && blocker.state === "blocked") blocker.reset(); }}>
        <DialogContent><DialogHeader><DialogTitle>保存 AI 设置？</DialogTitle><DialogDescription>当前设置尚未保存，保存失败时会保留输入并停留在本页。</DialogDescription></DialogHeader>
          {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
          <DialogFooter><Button variant="outline" disabled={Boolean(busy)} onClick={() => { if (blocker.state === "blocked") blocker.reset(); }}>继续编辑</Button><Button variant="outline" disabled={Boolean(busy)} onClick={() => { if (blocker.state === "blocked") blocker.proceed(); }}>放弃修改</Button><Button disabled={Boolean(busy)} onClick={async () => { if (await perform("save") && blocker.state === "blocked") blocker.proceed(); }}>保存并离开</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  </div>;
}
