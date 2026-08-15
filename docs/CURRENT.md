# 当前实现基线

本文件是当前应用、入口、数据位置和同步边界的唯一事实来源；其他说明文档应链接到这里，不自行维护“当前版本”结论。

## 当前应用

| 应用 | 源码 | 启动/构建 |
| --- | --- | --- |
| Windows 桌面端 | `diary_v2.0/` | `cd diary_v2.0 && python launcher.py`；前端 `cd Untitled && npm run build` |
| Android/iOS 移动端 | `mobile/` | `npm run android`；检查 `npm run typecheck && npm test` |

桌面端通过本地 HTTP API 使用 JSON 数据树；移动端使用应用私有 SQLite 作为工作副本。移动端仅显示日记、足迹、计划和数据管理；历史接单数据没有编辑 UI，但会继续保留在 SQLite、ZIP 备份、恢复和同步兼容路径中。

## 数据与同步

- 桌面端默认根目录：`diary_v2.0/data/Diary/`。优先级为 `LIFE_DIARY_DATA_ROOT`、`%LOCALAPPDATA%\\LifeDiary\\bootstrap.json`、默认目录。引导文件仅保存 `data_root`，绝不保存 API Key 或数据。
- 桌面端可在数据管理页复制到一个不存在的新目录；先生成安全备份，复制和校验成功后更新引导配置，重启后生效，旧目录保留。
- 移动端数据库和媒体始终保留在应用私有目录；外置目录只用于 Android SAF 输出 ZIP。
- Desktop 是 Canonical Source of Truth，Mobile 是 Working Copy。冲突必须经安全备份、解决和一次性提交后才导入；协议与历史接单兼容数据不可删除。

## 兼容与历史

- 根目录 `main.py` 和 `src/life_dairy/` 的旧 PySide6 UI 已冻结；其中 Storage、Models、Export、AI 等仍是桌面端兼容依赖，不能整体移动。
- Qt Android 旧工程位于 `legacy/mobile-qt/`；旧桌面 PySide6 UI 说明位于 `legacy/desktop-pyside/`。
- `docs/archive/` 中的文件都是历史材料，不能作为当前实现依据。
