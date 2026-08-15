import { useEffect, useState } from "react";
import { Activity, AlertTriangle, Database, Download, FileCheck, FolderOpen, GitMerge, Upload } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { AppSettings, DataRootStatus, Overview, SyncConflict, SyncSession, commitSyncImport, exportAllModules, exportDesktopCanonicalZip, getDataRootStatus, getOverview, getSettings, getSyncSession, importMobileSnapshot, migrateDataRoot, openDataRoot, resolveEntrySyncConflict, resolveGenericSyncConflict, selectDataRootDirectory, selectExportDirectory, selectMobileSnapshotZip } from "../lib/api";

export function DataManagement() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [dataRoot, setDataRoot] = useState<DataRootStatus | null>(null);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [exporting, setExporting] = useState(false);
  const [syncSession, setSyncSession] = useState<SyncSession | null>(null);
  const [mergeBodies, setMergeBodies] = useState<Record<string, string>>({});
  const [mergeTitles, setMergeTitles] = useState<Record<string, string>>({});
  const [syncBusy, setSyncBusy] = useState(false);
  const [message, setMessage] = useState("正在检查数据");

  useEffect(() => {
    getOverview()
      .then((data) => {
        setOverview(data);
        setMessage(data.migrated_from_legacy ? "首次启动已从旧版目录迁移数据" : "2.0 数据目录可用");
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "读取失败"));
    getSettings().then(setSettings).catch(() => undefined);
    getDataRootStatus().then(setDataRoot).catch(() => undefined);
  }, []);

  async function handleOpenDataRoot() {
    try {
      await openDataRoot();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "打开数据目录失败");
    }
  }

  async function handleMigrateDataRoot() {
    try {
      const selected = await selectDataRootDirectory();
      const result = await migrateDataRoot(selected.selected_path);
      setMessage(`已复制到新目录；安全备份：${result.safety_backup}。请重启应用后生效，原目录将保留。`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "迁移数据目录失败");
    }
  }

  async function handleSelectExportDir() {
    try {
      const next = await selectExportDirectory();
      setSettings(next);
      setMessage("导出位置已保存");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "选择导出位置失败");
    }
  }

  async function handleExportAll() {
    setExporting(true);
    try {
      const result = await exportAllModules();
      window.alert(`全部导出完成，共 ${result.count ?? 0} 条记录\n\n目录：${result.output_dir ?? ""}\n原始数据 ZIP：${result.zip_path ?? ""}`);
      setMessage("全部板块已导出");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "全部导出失败");
    } finally {
      setExporting(false);
    }
  }

  async function refreshSession(sessionId: string) {
    const next = await getSyncSession(sessionId);
    setSyncSession(next);
    setMergeBodies((current) => {
      const updated = { ...current };
      next.conflicts.forEach((conflict) => {
        if (updated[conflict.id] === undefined) updated[conflict.id] = conflict.merge_candidate ?? conflict.desktop.body;
      });
      return updated;
    });
    setMergeTitles((current) => {
      const updated = { ...current };
      next.conflicts.forEach((conflict) => {
        if (updated[conflict.id] === undefined) updated[conflict.id] = conflict.desktop.title ?? "";
      });
      return updated;
    });
  }

  async function handleMobileImport() {
    setSyncBusy(true);
    try {
      const selected = await selectMobileSnapshotZip();
      const session = await importMobileSnapshot(selected.zip_path);
      setSyncSession(session);
      setMergeBodies(Object.fromEntries(session.conflicts.map((conflict) => [conflict.id, conflict.merge_candidate ?? conflict.desktop.body])));
      setMergeTitles(Object.fromEntries(session.conflicts.map((conflict) => [conflict.id, conflict.desktop.title ?? ""])));
      setMessage(`手机版导入已预检：${session.summary.conflict} 个待处理冲突。安全备份：${session.safety_backup}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "手机版 ZIP 导入失败");
    } finally {
      setSyncBusy(false);
    }
  }

  async function resolveEntry(conflict: SyncConflict, choice?: "desktop" | "mobile") {
    if (!syncSession) return;
    setSyncBusy(true);
    try {
      const body = choice === "desktop" ? conflict.desktop.body : choice === "mobile" ? conflict.mobile.body : mergeBodies[conflict.id] ?? "";
      const title = choice === "desktop" ? conflict.desktop.title ?? "" : choice === "mobile" ? conflict.mobile.title ?? "" : mergeTitles[conflict.id] ?? "";
      await resolveEntrySyncConflict(syncSession.id, conflict.id, body, title);
      await refreshSession(syncSession.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存冲突解决结果失败");
    } finally {
      setSyncBusy(false);
    }
  }

  async function resolveGeneric(conflict: SyncConflict, choice: "desktop" | "mobile") {
    if (!syncSession) return;
    setSyncBusy(true);
    try {
      await resolveGenericSyncConflict(syncSession.id, conflict.id, choice);
      await refreshSession(syncSession.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存冲突解决结果失败");
    } finally {
      setSyncBusy(false);
    }
  }

  async function handleCommitSync() {
    if (!syncSession) return;
    setSyncBusy(true);
    try {
      await commitSyncImport(syncSession.id);
      await refreshSession(syncSession.id);
      setMessage("手机版导入已一次性提交到 Desktop Canonical 数据库。");
      getOverview().then(setOverview).catch(() => undefined);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "提交导入失败");
    } finally {
      setSyncBusy(false);
    }
  }

  async function handleExportCanonical() {
    setSyncBusy(true);
    try {
      const result = await exportDesktopCanonicalZip();
      setMessage(`Desktop Canonical ZIP 已生成：${result.zip_path}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "生成手机同步包失败");
    } finally {
      setSyncBusy(false);
    }
  }

  function renderVersion(body: string, changedLines: number[] | undefined, changedClass: string) {
    const changed = new Set(changedLines ?? []);
    return <pre className="min-h-48 max-h-96 overflow-auto whitespace-pre-wrap text-sm leading-6">{(body.split("\n").length ? body.split("\n") : [""]).map((line, index) => <span key={index} className={changed.has(index) ? `${changedClass} block px-1` : "block px-1"}>{line || " "}</span>)}</pre>;
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-semibold">数据管理</h1>
          <p className="text-muted-foreground mt-2">2.0 使用独立数据目录，首次启动自动从旧版迁移。</p>
          <p className="text-xs text-muted-foreground mt-1">桌面版 {overview?.build.version ?? "dev"} · 提交 {overview?.build.commit ?? "unknown"}</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitMerge className="size-5" />
              手机版同步
            </CardTitle>
            <CardDescription>Desktop 为唯一 Canonical 主库。导入只在所有冲突解决后一次性提交。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3">
              <Button onClick={handleMobileImport} disabled={syncBusy}>
                <Upload className="size-4" />
                导入手机版 ZIP
              </Button>
              <Button variant="outline" onClick={handleExportCanonical} disabled={syncBusy}>
                <Download className="size-4" />
                生成手机同步包
              </Button>
            </div>
            {syncSession && <>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-sm">
                {Object.entries(syncSession.summary).map(([key, count]) => <div className="rounded bg-secondary p-3" key={key}><p className="text-muted-foreground">{key}</p><p className="text-lg font-semibold">{count}</p></div>)}
              </div>
              <p className="text-xs text-muted-foreground break-all">导入前安全备份：{syncSession.safety_backup}</p>
              {syncSession.conflicts.map((conflict) => <div key={conflict.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div><p className="font-semibold">{conflict.module === "entries" ? `日记 ${conflict.desktop.id}` : `${conflict.module} ${conflict.canonical_id}`}</p><p className="text-sm text-muted-foreground">{conflict.reason}；PC ID 将保留为 {conflict.canonical_id}</p></div>
                  <span className={conflict.resolved ? "text-green-600 text-sm" : "text-orange-600 text-sm"}>{conflict.resolved ? "已解决" : "待处理"}</span>
                </div>
                {conflict.module === "entries" ? <>
                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
                    <div className="rounded border"><p className="px-3 py-2 font-medium bg-secondary">PC 当前版本（只读）</p><p className="px-3 py-2 border-b text-sm font-medium">{conflict.desktop.title}</p>{renderVersion(conflict.desktop.body, conflict.desktop_changed_lines, "bg-red-100 dark:bg-red-950")}</div>
                    <div className="rounded border"><p className="px-3 py-2 font-medium bg-secondary">最终合并结果（可编辑）</p><input className="w-full border-b p-3 bg-transparent text-sm font-medium" value={mergeTitles[conflict.id] ?? conflict.desktop.title ?? ""} onChange={(event) => setMergeTitles((current) => ({ ...current, [conflict.id]: event.target.value }))} disabled={conflict.resolved || syncBusy} aria-label="最终标题" /><textarea className="w-full min-h-48 p-3 bg-transparent text-sm leading-6" value={mergeBodies[conflict.id] ?? conflict.merge_candidate ?? conflict.desktop.body} onChange={(event) => setMergeBodies((current) => ({ ...current, [conflict.id]: event.target.value }))} disabled={conflict.resolved || syncBusy} /></div>
                    <div className="rounded border"><p className="px-3 py-2 font-medium bg-secondary">Mobile 版本（只读）</p><p className="px-3 py-2 border-b text-sm font-medium">{conflict.mobile.title}</p>{renderVersion(conflict.mobile.body, conflict.mobile_changed_lines, "bg-green-100 dark:bg-green-950")}</div>
                  </div>
                  <div className="flex flex-wrap gap-2"><Button size="sm" variant="outline" disabled={conflict.resolved || syncBusy} onClick={() => resolveEntry(conflict, "desktop")}>采用电脑版本</Button><Button size="sm" variant="outline" disabled={conflict.resolved || syncBusy} onClick={() => resolveEntry(conflict, "mobile")}>采用手机版本</Button><Button size="sm" disabled={conflict.resolved || syncBusy} onClick={() => resolveEntry(conflict)}>保存并解决</Button></div>
                </> : <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3"><pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded bg-secondary p-3 text-xs">{conflict.desktop.body}</pre><pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded bg-secondary p-3 text-xs">{conflict.mobile.body}</pre></div>
                  <div className="flex gap-2"><Button size="sm" variant="outline" disabled={conflict.resolved || syncBusy} onClick={() => resolveGeneric(conflict, "desktop")}>保留电脑版本</Button><Button size="sm" variant="outline" disabled={conflict.resolved || syncBusy} onClick={() => resolveGeneric(conflict, "mobile")}>采用手机版本</Button></div>
                </>}
              </div>)}
              <Button disabled={syncBusy || Boolean(syncSession.committed_at) || syncSession.conflicts.some((conflict) => !conflict.resolved)} onClick={handleCommitSync}>一次性 Commit Import</Button>
            </>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="size-5" />
              数据位置
            </CardTitle>
            <CardDescription>数据根目录可迁移；切换在重启后生效，旧目录不会被删除。</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">2.0 数据目录</p>
              <div className="p-4 bg-secondary rounded-lg font-mono text-sm break-all">
                {dataRoot?.data_root || overview?.data_root || "diary_v2.0/data/Diary"}
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
            <Button variant="outline" onClick={handleMigrateDataRoot}>
              <FolderOpen className="size-4" />
              选择新目录并迁移当前数据
            </Button>
            <p className="text-xs text-muted-foreground">当前来源：{dataRoot?.source ?? "default"}；引导配置：{dataRoot?.bootstrap_path ?? "系统本地配置"}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="size-5" />
              导出位置
            </CardTitle>
            <CardDescription>以后 Word 和 PDF 全量导出会直接保存到这里</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-secondary rounded-lg font-mono text-sm break-all">
              {settings?.export_dir || `${overview?.data_root || "diary_v2.0/data/Diary"}\\exports`}
            </div>
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={handleSelectExportDir}>
              <FolderOpen className="size-4" />
              选择导出位置
              </Button>
              <Button onClick={handleExportAll} disabled={exporting}>
                <Download className="size-4" />
                {exporting ? "导出中" : "全部导出"}
              </Button>
            </div>
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
