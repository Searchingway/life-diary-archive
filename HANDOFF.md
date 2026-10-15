## Sync Protocol V1: Desktop Canonical + Plan V2

### 修改文件
- `docs/sync/SYNC_PROTOCOL_V1.md` — 定义 Protocol V1、共享模块边界、兼容策略与冲突规则。
- `shared/sync/fixtures/plan_v2_full.json` — 跨平台共用的 Canonical Plan V2 fixture。
- `diary_v2.0/plan_v2.py` — 无损且幂等的 Plan V1 到 V2 迁移与进度计算。
- `diary_v2.0/sync_service.py` — ZIP 预检、安全备份、staged session、冲突处理、一次性提交与 Canonical ZIP。
- `diary_v2.0/data_api.py` — Desktop 轻计划保存时升级为 Plan V2。
- `diary_v2.0/server.py` — 同步 session、冲突解决与 Canonical ZIP API。
- `diary_v2.0/Untitled/src/app/lib/api.ts`、`pages/DataManagement.tsx` — Desktop 同步导入、统计、三栏冲突解决器与导出 UI。
- `tests/test_sync_protocol_v1.py` — Protocol/Plan/import/canonical ZIP 回归覆盖。

### 测试结果
- `python -m unittest discover -s tests -v`: 141 passed。
- `cd diary_v2.0/Untitled && npm run build`: passed。
- `python -m py_compile diary_v2.0/data_api.py diary_v2.0/sync_service.py diary_v2.0/server.py`: passed。

### 风险
- 旧 Expo 备份 manifest 作为 legacy mobile snapshot 兼容读取；Desktop 输出始终为正式 Protocol V1 manifest。
- `entries` 支持正文两端 diff、可编辑合并和图片 hash 并集。其他共享模块若同 ID 内容不同，将保守地要求选择完整 PC 或 Mobile 版本，避免无 ancestor 的自动覆盖。
- staged session 是服务进程内会话；重启服务会使未提交 session 失效，正式数据不受影响，可重新从 ZIP 开始。

### 是否建议 commit
是；建议 message：`feat: add desktop canonical sync protocol v1`

## Desktop Sync Protocol V1 acceptance fixes

### 修改文件
- `diary_v2.0/plan_v2.py` — Canonicalize `搁置`/`暂停`, `普通`, and `reduce`; remove known V1 aliases without dropping unknown extensions.
- `diary_v2.0/Untitled/src/app/pages/LightPlan.tsx` — Read, edit, and save Plan V2 title/goal/dates/status/priority/notes/tasks and canonical add/subtract values while preserving advanced fields and tags.
- `diary_v2.0/sync_service.py`, `server.py`, `data_api.py` — Full footprint semantic fingerprinting, official restorable safety backup, non-lossy entry conflict candidate/title/image labels, session cleanup, and global HTTP mutation/commit locking.
- `src/life_dairy/backup_service.py` — 旧版修复：allow the official empty-Desktop backup manifest created before a first import to validate and restore normally.
- `diary_v2.0/Untitled/src/app/lib/api.ts`, `pages/DataManagement.tsx` — Three-column entry conflict title and body resolution contract.
- `docs/sync/SYNC_PROTOCOL_V1.md`, `tests/test_sync_protocol_v1.py` — Document canonical aliases and add acceptance regression coverage.

### 测试结果
- `python -m unittest discover -s tests -v`: 147 passed, 0 failed; the final image-label fallback assertion was then rerun in `tests.test_sync_protocol_v1` (15 passed).
- `cd diary_v2.0/Untitled && npm run build`: passed.
- `python -m py_compile diary_v2.0/data_api.py diary_v2.0/plan_v2.py diary_v2.0/sync_service.py diary_v2.0/server.py src/life_dairy/backup_service.py`: passed.

### 风险
- 同步 commit obtains a process-wide mutation lock. Long imports intentionally block concurrent HTTP writes until the directory swap is complete.
- All prepared-session bulk trees are removed after a successful commit; only `session.json` metadata and the official safety ZIP remain.

### 是否建议 commit
是；建议 message：`fix(sync): complete desktop protocol v1 acceptance`。本轮未推送。

## Mobile 2.3.0 Sync Protocol V1

### 修改文件
- `mobile/src/compat/syncProtocol.ts`, `mobile/src/services/backup.ts` — Mobile Snapshot 与 Desktop Canonical ZIP 的 V1 manifest、Plan V2 canonical migration、共享模块预览和先备份后替换导入。
- `mobile/src/compat/incomingIntent.ts`, `mobile/src/app/+native-intent.ts`, `mobile/src/app/(tabs)/data.tsx` — Android ZIP VIEW/SEND URI 路由、去重和数据页手动导入入口。
- `mobile/src/domain/plans.ts`, `mobile/src/app/(tabs)/plans.tsx`, `mobile/src/db/repository.ts`, `mobile/src/compat/archive.ts` — Plan V2 字段/别名兼容、canonical 写入和仅替换共享模块。
- `mobile/app.json`, `mobile/package*.json`, `mobile/README.md`, `mobile/FAQ_APK.md`, `mobile/scripts/build-release.ps1` — 2.3.0 (5)、ZIP intent filters、交付路径及本地 APK 不入 Git 说明。
- `mobile/src/__tests__/syncProtocol.test.ts`, `archive.test.ts`, `plans.test.ts`, `repository.test.ts` — 协议、fixture、迁移、URI、导入替换和 Today 回归覆盖。

### 测试结果
- `npm run typecheck`：通过。
- `npm test`：5 files / 19 tests passed。
- `npx expo export --platform android`：通过。
- `npx expo prebuild --platform android --clean --no-install`：通过；生成的 AndroidManifest 包含 ZIP VIEW/SEND 过滤器。
- `:app:assembleRelease`：通过（仅本次构建使用完整的本机 NDK 27.2.12479018 覆盖，以避开损坏的 27.1.12297006 安装）。
- APK：`mobile/build-output/LifeDiary-Mobile-2.3.0.apk`，`aapt` 验证 `com.localfirst.lifediary` / `2.3.0 (5)`，v2 签名有效，SHA-256 为 `C60DD2993B3651604F2F0BA9CD093FAEF97B21E24B9771F77EF247A55CD5041A`。

### 风险
- Release APK 使用 Android Debug 签名；本机没有正式 release keystore。历史 2.2 APK 的证书未在本轮临时提取比对，因此能否与旧安装包覆盖升级须在实际设备上确认。
- 未检测到 ADB 已连接设备，未执行安装或启动验收。
- 产物位于 ignored 的 `mobile/build-output/`，不提交 Git。

### 是否建议 commit
是；建议 message：`feat(mobile): implement sync protocol v1 2.3`。本轮未提交或推送。


## 2026-10-15 桌面可靠性优化：资源清空与原始 ZIP

### 修改文件
- `diary_v2.0/data_api.py` — 区分未传入字段与显式空字符串，轻资源的综合判断、主观感受、备注支持清空；保留未传入字段及扩展数据。
- `diary_v2.0/export_service.py` — 原始 ZIP 排除自身及数据目录内的自定义输出子目录；按路径边界排除 exports，保留 exports-notes 等正常目录。
- `tests/test_diary_v2_backend_safety.py`、`tests/test_v2_export_service.py` — 清空/保留字段和嵌套导出回归。

### 测试结果
- 修改前完整基线：`python -m pytest tests/ -q --tb=short`，149 passed，6 subtests passed。
- 先复现：新回归 3 failed、1 passed；修复后相关测试 20 passed，6 subtests passed。
- 测试通过环境变量及临时目录隔离；未读取、迁移或修改真实用户数据。

### 风险
- 原始 ZIP 仍为原有完整本地数据备份，含配置，分享前应由用户检查；本轮不改变备份格式。
- 数据目录内作为输出位置的子目录整体排除，避免历史输出重复打包；建议使用专用导出目录。

### 是否建议 commit
是：`fix(desktop): preserve cleared resource fields and exclude recursive exports`。


## 2026-10-15 日记草稿保护与保存状态

### 修改文件
- `diary_v2.0/Untitled/src/app/App.tsx` — 使用 React Router 的 data router，保留既有路由，支持拦截未保存日记的站内导航。
- `diary_v2.0/Untitled/src/app/pages/Diary.tsx` — 搜索、切换日记、新建、侧栏导航统一提供保存、放弃、取消；保存失败留在原页；异步搜索不覆盖新编辑，显示保存/加载状态，支持通过 id 定位日记。
- `diary_v2.0/Untitled/src/app/lib/saveCoordinator.ts`、`saveCoordinator.test.ts` — 放弃切换前等待已有保存队列完成。
- `HANDOFF.md` — 同步交付证据，并修正上一批新增交接段落的终端编码问题。

### 测试结果
- 浏览器先复现搜索直接移除未保存编辑器；新增等待队列测试先失败后通过。
- Vitest：7 passed；`npm run build`：通过。
- 隔离数据浏览器验证：搜索拦截、取消切换、侧栏拦截、保存失败保留草稿、保存并跳转、放弃不写入。

### 风险
- 新保护覆盖日记页；其他模块各自的编辑流程尚需后续逐项完善。
- 自动保存已发出的请求会先完成，再执行放弃切换；放弃不会撤销已成功保存的内容。
- 测试仅使用 `.tmp_testdata/`，未触碰真实日记或 AI 配置；未做桌面壳与安卓真机验收。

### 是否建议 commit
是：`fix(diary): protect unsaved drafts during search and navigation`。
