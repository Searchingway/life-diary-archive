## Why

当前桌面端是 PySide6 Widgets + QTabWidget 的直接组件模式。UI 和业务逻辑在同一进程，前端代码重复 13 次（无 BasePage 抽象），修改 UI 需要改 Python 代码并重新打包。

Desktop Next 的目标：**在不改 Storage 层的前提下**，将 UI 层迁移到 React SPA，通过 Python HTTP API 与后端通信。

## What Changes

- **新增** `diary_v2.0/` 作为主入口（已有 launcher.py、React 前端、data_api.py、server.py、export_service.py）
- **新增** React 前端页面 14 个（基于 `diary_v2.0/Untitled/`）
- **新增** OpenSpec 规格体系（本变更）
- **删除** `src/life_dairy/` 中不再使用的 Page 类（保留 Storage/Export 层）
- **保留** `data/Diary/` 数据目录不变
- **保留** `src/life_dairy/action_plan_storage.py`、`ai_service.py`、`exporters.py`、`models.py` 等后端模块

## Capabilities

### New Capabilities
- `react-frontend`: 14 个 React SPA 页面，通过 REST API 与后端通信
- `state-model`: 每个页面使用 `state + event → newState → view` 状态模型
- `openspec-specs`: 系统规格 + 变更管理的 OpenSpec 体系

### Preserved Capabilities
- `storage-json`: 保持 JSON 文件系统不变
- `ai-deepseek`: AI 功能通过后端代理，前端只调 API
- `export-word-pdf`: 导出通过后端 API

## Impact

- `openspec/`：新增 specs/ + changes/ 目录结构
- `diary_v2.0/`：React 页面 + 状态模型实现（后续完成）
- `src/life_dairy/`：只保留 Storage/Export/AI 层，Page 类标记为废弃
- `docs/`：状态模型文档迁移到 OpenSpec 体系
