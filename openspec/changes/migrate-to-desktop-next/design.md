## Context

旧版 `src/life_dairy/` 从 3.0 到 4.0 积累了 40 个文件和约 14,000 行 Python 代码。4.0 重构已经将 `diary_v2.0/` 设为主入口，但前端页面（React SPA）尚未完成，目前依赖旧版 PySide6 页面。

本变更的目标：**正式确立 Desktop Next 架构，完成 OpenSpec 规格体系，后续在前端实现所有页面**。

## Goals / Non-Goals

**Goals:**
- 建立 OpenSpec 规格体系（specs/ + changes/）
- 明确桌面端三层架构（Frontend + Backend + Storage）
- 为每个页面编写状态模型（state + event → newState → view）
- 为 ActionPlan 编写 three-view 规格（today / gantt / chain）

**Non-Goals:**
- 不实现 React 页面（本变更只写规格）
- 不修改 `src/life_dairy/` 代码（保留兼容引用）
- 不修改 `data/Diary/` 数据
- 不删除旧版 Page 类（先标记为废弃）
- 不升级依赖（PySide6、python-docx 等保持当前版本）

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Desktop Shell                      │
│  PySide6 + QWebEngineView (diary_v2.0/launcher.py)  │
│  ┌───────────────────────────────────────────────┐  │
│  │            React SPA (TypeScript)             │  │
│  │  ┌──────┐ ┌──────┐ ┌──────────┐ ┌──────┐   │  │
│  │  │Dashboard│ │Diary│ │ActionPlan│ │ ...  │   │  │
│  │  └───┬──┘ └──┬──┘ └────┬─────┘ └──┬──┘   │  │
│  │      └────────┴─────────┴──────────┘      │  │
│  │                  │ HTTP REST               │  │
│  └──────────────────┼────────────────────────┘  │
└─────────────────────┼───────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────┐
│          Python HTTP Server (server.py)          │
│  ┌──────────────────┼────────────────────────┐  │
│  │     data_api.py + export_service.py        │  │
│  └──────────────────┼────────────────────────┘  │
│                     │ import                    │
│  ┌──────────────────┼────────────────────────┐  │
│  │    src/life_dairy/ (Storage / Export / AI) │  │
│  └──────────────────┼────────────────────────┘  │
└─────────────────────┼───────────────────────────┘
                      │
               data/Diary/ (JSON Files)
```

## State Model Principles

1. **All pages use `state + event → newState → view`**
2. Draft state 和 server state 严格分离
3. AI preview 必须有独立状态层，不能直接写入正式数据
4. Effect 通过 SUCCESS / FAILED 事件修改 state，不直接修改 view
5. Derived state 由 reducer 在 return 时计算，不单独维护

## OpenSpec Directory

```
openspec/
  config.yaml
  specs/
    desktop-legacy/spec.md          # 当前事实
    desktop-next/spec.md            # 目标架构
    action-plan/spec.md             # ActionPlan 需求 + Scenario
    ai-preview/spec.md              # AI 预览弹窗需求
    data-contract/spec.md           # API 数据契约
  changes/
    archive/                        # 已归档变更（不动）
    migrate-to-desktop-next/        # 架构迁移
      .openspec.yaml
      proposal.md
      design.md
      state-model.md
      tasks.md
      specs/                        # 绑定的 spec 副本
        desktop-next/spec.md
        action-plan/spec.md
        data-contract/spec.md
    action-plan-v2/                 # ActionPlan 三视图
      .openspec.yaml
      proposal.md
      design.md
      state-model.md
      tasks.md
      specs/
        action-plan/spec.md
```

## Decisions

1. **specs/ 写事实，changes/ 写变更** — specs 描述系统当前应然状态，changes 描述从当前状态到目标状态的迁移
2. **变更绑定 spec 副本** — 每个 change 下复制相关 spec，变更自包含
3. **状态模型在 changes/ 中维护** — 每个 change 的 `state-model.md` 描述该变更涉及页面的状态转移
4. **页面规范用 Requirement + Scenario 写法** — 不写 UI 细节，写行为
5. **React 路由用 `/` + 页面名** — 与 API 路径一致，减少心智负担
