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
# 仓库治理、数据根目录与移动端基础体验

### 修改文件
- `docs/CURRENT.md`、README 与开发说明 — 统一当前应用、数据和同步事实来源，并归档历史文档。
- `diary_v2.0/data_root_config.py`、`data_api.py`、`server.py`、数据管理页 — 安全迁移数据根目录，外置 bootstrap 配置与重启生效。
- `mobile/` — 修复外部 URI 路由、段首缩进、离开编辑页自动保存、SAF 外置备份和构建标识。
- `legacy/` — 收纳 Qt Android 工程和冻结的 PySide6 UI 说明。

### 测试结果
- Python: `D:\\python\\python.exe -m pytest tests/ -v --tb=short`，153 passed。
- Mobile: `npm run typecheck` 通过；`npm test` 24 passed。

### 风险
- 桌面目录选择和 Android SAF 需要在目标设备上进行一次手工验证；代码测试未覆盖系统对话框。

### 是否建议 commit
是，建议 message：`chore: align active apps, storage, mobile startup and legacy structure`
