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
