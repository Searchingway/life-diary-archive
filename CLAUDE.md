# CLAUDE.md

当前应用和数据事实请先读 [docs/CURRENT.md](docs/CURRENT.md)；本文件只定义仓库协作规则。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run full test suite
python -m pytest tests/ -v --tb=short

# Run a single test file
python -m pytest tests/test_action_plan_storage.py -v --tb=short

# Run a single test
python -m pytest tests/test_ai_service.py::AIServiceConfigTests::test_save_and_load_settings_roundtrip -v

# Start the app (current, recommended)
cd diary_v2.0 && python launcher.py

# Frontend build (after npm install)
cd diary_v2.0/Untitled && npm install && npm run build

# Frontend dev mode
cd diary_v2.0/Untitled && npm run dev

# Install Python deps
pip install -r diary_v2.0/requirements.txt

# Verify backend server starts (headless check)
cd diary_v2.0 && python -c "from server import start_server; s=start_server(); print(f'OK port {s.server_port}'); s.shutdown()"
```

**注意**：根目录 `python main.py` 是旧版 PySide6 入口，已废弃，不使用。

## Architecture

### 新版三层（diary_v2.0/，推荐）

```
React SPA (TypeScript + MUI + Radix + Tailwind)
      ↕ HTTP REST JSON
server.py (路由分发，不包含业务逻辑)
      ↕ 函数调用
data_api.py (CRUD + 业务逻辑 — 最核心的文件)
export_service.py (导出功能)
      ↕ import
src/life_dairy/ (旧版 Storage/Export/AI 层，冻结)
      ↕
JSON 文件系统
```

各文件职责：

| 文件 | 职责 |
|------|------|
| `launcher.py` | PySide6 桌面壳（~43 行），启动 HTTP 服务器 + 打开 QWebEngineView |
| `server.py` | HTTP 路由分发（LifeDiaryHandler），不包含业务逻辑 |
| `data_api.py` | 模块配置、CRUD、统计、图片操作、footprint 操作、通用 save/delete |
| `export_service.py` | 导出功能（Word/PDF/TXT/Markdown/ZIP） |
| `src/life_dairy/` | 旧版 Storage/Export/AI/Models 层，作为兼容后端被导入 |

### 启动流程

```
launcher.py → start_server() → ThreadingHTTPServer(LifeDiaryHandler)
                                  ↓
                            data_api / export_service 函数
                                  ↓
                            src/life_dairy (Storage)
                                  ↓
                            日记/行动计划的 JSON 目录
```

launcher.py 只是桌面壳，去掉它 server.py 可以独立运行（只是没有桌面窗口）。

## Startup

- **新版（推荐）**：`cd diary_v2.0 && pip install -r requirements.txt && python launcher.py`
- **旧版入口** `python main.py`（根目录）已废弃，不使用

## Frontend

- 包管理器：**npm**（有 `package-lock.json`，无 `pnpm-lock.yaml`）
- `cd diary_v2.0/Untitled && npm install && npm run build` 构建
- `npm run dev` 开发模式（需配合后端运行）

## Data

- **真实数据源**：`diary_v2.0/data/Diary/`
- **根目录 `data/Diary/` 是旧版遗留**，两套已不同步（v2 版含 46 篇日记，旧版 39 篇）
- 两套数据**都不能**随意删除、迁移、覆盖
- 测试**必须**使用 `.tmp_testdata/` 临时目录，不得读写真实数据
- `data/` 和 `diary_v2.0/data/` 都在 `.gitignore` 中

## API Key 安全

- `diary_v2.0/data/Diary/config/ai_settings.json` 可能存在真实 API Key
- 该文件和整个 `diary_v2.0/data/` 视为真实用户数据
- **不得提交**到 Git
- **不得在日志、文档、测试输出、commit message 中打印完整 API Key**
- 如需展示，必须使用掩码，例如 `sk-****abcd`

## OpenSpec

以下情况**必须先读 `openspec/`**：

- 修改或新增数据字段 / JSON 结构
- 新增或修改 API 端点
- 新增或修改 AI 功能（提示词、调用流程、预览方式）
- 修改或新增行动计划
- 修改导入导出（ZIP/Word/PDF/TXT）
- 涉及两个以上模块的改动

以下情况不需要：

- 轻量文案修改
- 单个页面的 UI 调整（不涉及数据字段）
- 纯测试用例新增

## Lifecycle Models

当任务涉及页面交互、弹窗、自动保存、图片管理、AI 预览、数据导入导出、ActionPlan、复杂状态流转时，**必须先读取对应的生命周期文档**：

### 通用优先级

```
最高: OpenSpec change 下的 lifecycle.md（如 action-plan-v2/lifecycle.md）
中:   OpenSpec change 下的 state-model.md
中:   docs/lifecycle/COMMON_LIFECYCLE.md（通用生命周期）
低:   docs/lifecycle/PAGE_LIFECYCLES.md（页面专用生命周期）
低:   docs/CURRENT.md（当前应用与数据事实）
```

### 必须读取的文档

| 场景 | 必须读取 |
|------|---------|
| 页面交互 / 弹窗 / 自动保存 | `docs/lifecycle/COMMON_LIFECYCLE.md`、`docs/lifecycle/PAGE_LIFECYCLES.md` |
| 图片管理 | `docs/lifecycle/COMMON_LIFECYCLE.md`（Attachment / Image Lifecycle） |
| AI 预览 | `docs/lifecycle/COMMON_LIFECYCLE.md`（AI Preview Lifecycle） |
| 数据导入导出 | `docs/lifecycle/PAGE_LIFECYCLES.md`（DataManager） |
| ActionPlan 三视图 | `openspec/changes/action-plan-v2/lifecycle.md`（**最高优先级**） |

## 旧版规则

根目录 `main.py` 和 `src/life_dairy/` 是旧版 PySide6 Widgets 代码，**已冻结**：

- **禁止**旧版 PySide6 UI 重构（Page 类、QWidget 布局）
- **禁止**随意新增旧 Page 功能
- **仅允许**以下情况的修改（需说明原因）：
  - Storage 层 bug 影响新版数据读写
  - Export 层 bug（新版 export_service.py 依赖它）
  - AI 服务层 bug（`ai_service.py`）
  - Models 数据类兼容问题
- 修改时必须在 commit message 中注明"旧版修复：原因"

## ActionPlan

ActionPlan（行动计划）是轻计划（LightPlan）的**执行层**：
- 轻计划回答"我想做什么"
- ActionPlan 回答"我什么时候做、做到哪了"

ActionPlan 是**执行工作台**，不是 CRUD 表单：

- 必须围绕 `today / gantt / chain` 三种视图设计
- 甘特图使用 `startDate / endDate / progress` 决定任务条位置和宽度（**不允许用 `estimatedMinutes`**）
- 不允许把行动计划主界面做成大表单
- 新增 ActionPlan 交互必须使用三视图模式

实现或修改 ActionPlan 的以下功能前，**必须先读取**对应的 OpenSpec 文件：
- today / gantt / chain 三视图 → `openspec/specs/action-plan/spec.md` + `openspec/changes/action-plan-v2/`
- 任务数据结构 → `openspec/specs/action-plan/spec.md`
- AI 拆解 → `openspec/changes/action-plan-v2/proposal.md` + `openspec/changes/action-plan-v2/state-model.md`
- 甘特图拖拽 / 任务链节点 → `openspec/changes/action-plan-v2/design.md` + `openspec/changes/action-plan-v2/tasks.md`

需要读取的具体文件：

| 场景 | 必须读取 |
|------|---------|
| 三视图交互 | `openspec/specs/action-plan/spec.md`、`openspec/changes/action-plan-v2/proposal.md`、`openspec/changes/action-plan-v2/design.md` |
| 状态模型 | `openspec/changes/action-plan-v2/state-model.md` |
| AI 拆解 | `openspec/changes/action-plan-v2/proposal.md`、`openspec/changes/action-plan-v2/state-model.md` |
| 任务实现 | `openspec/changes/action-plan-v2/tasks.md` |

## Testing

- **最低验收**：`python -m pytest tests/test_<改动模块>.py -v --tb=short`
- **完整验收**：`python -m pytest tests/ -v --tb=short`
- **React 前端改动**：`cd diary_v2.0/Untitled && npm run build`
- **不允许声称测试通过，除非实际运行过**
- **已知失败**（4 个，均为旧版 work/entry 模块的编码和排序问题，非本轮引入）：

| 测试 | 原因 |
|------|------|
| `test_work_changes_can_auto_save...` | KeyError: 'one_sentence' |
| `test_list_entries_in_date_range...` | 排序断言不一致 |
| `test_list_works_can_search...` | 编码问题 |
| `test_save_and_reload_work_with_relations` | 编码问题 |

**验收标准**：新增测试必须全部通过，已知失败数量不得增加。

## HANDOFF

以下情况**必须更新 `HANDOFF.md`**：

- 新增模块
- 新增文件超过 3 个
- 重大架构变更
- 数据格式变更
- OpenSpec 规格变更

以下情况也必须在本轮提交前更新 `HANDOFF.md` 或在完成报告中说明：

- 修改 CLAUDE.md
- 修改 OpenSpec
- 修改启动入口 / 包管理 / 数据目录规则
- 修改测试验收规则
- 修复真实数据 / API Key / .gitignore 相关安全问题

更新格式：

```markdown
## 版本/变更标题

### 修改文件
- path — 原因

### 测试结果
- pytest: X/Y passed, Z failed (已有失败)

### 风险
- ...

### 是否建议 commit
是/否，建议 message 内容
```
