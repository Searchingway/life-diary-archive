# Desktop Next — 系统规格

> 版本：Next
> 状态：**设计中**。目标架构。

## Architecture

```
React SPA (TypeScript + Vite + MUI)
       │ HTTP REST API (JSON)
Python HTTP Server (http.server.ThreadingHTTPServer)
       │ import
Legacy Storage Layer (src/life_dairy/*)
       │
JSON File System (data/Diary/)
       ▲
PySide6 + QWebEngineView (Desktop Shell)
```

### 三层分离

| 层 | 技术 | 职责 |
|----|------|------|
| **Frontend** | React 18 + TypeScript + MUI 7 + Radix UI + Tailwind CSS 4 | 页面渲染、用户交互、状态管理、路由 |
| **Backend** | Python http.server + data_api.py + export_service.py | REST API、数据 CRUD、导出、AI 调用 |
| **Storage** | `src/life_dairy/*`（未改动） | JSON 文件读写、数据模型、历史兼容 |

### 通信

- 前端 → 后端：HTTP REST（`/api/modules/<key>`、`/api/overview`、`/api/settings` 等）
- 后端 → 前端：JSON response
- 后端 → 存储：函数调用（import `src/life_dairy`）
- 无 WebSocket、无 SSE、无实时推送

## Page Inventory

| 页面 | 路由 | 类型 |
|------|------|------|
| Dashboard | `/` | 统计 + 时间线 |
| Diary | `/diary` | CRUD + 图片 |
| Footprint | `/footprints` | CRUD + visits |
| LightPlan | `/plans` | CRUD + AI |
| ActionPlan | `/action-plans` | CRUD + today/gantt/chain + AI |
| LightThought | `/thoughts` | CRUD + ideas + AI |
| LightResource | `/resources` | CRUD + resource items + AI |
| InfoMemo | `/info-memos` | CRUD + type-linked status |
| SelfObservation | `/observations` | CRUD + emotion/intensity |
| LessonsReflection | `/lessons` | CRUD + category/severity |
| SelfAnalysis | `/self-analysis` | CRUD + 12-section form |
| WorksReflection | `/works` | CRUD + work type |
| DataManager | `/data` | health check + backup/restore |
| AISettings | dialog | API key + model config |

## Design Principles

1. **数据不改**：Storage 层完全复用 `src/life_dairy/`，不改动 JSON 结构和软删除逻辑
2. **前后端分离**：前端只负责渲染和交互，不直接读写文件
3. **状态驱动**：每个页面使用 `state + event → newState → view` 模型
4. **AI 预览确认**：AI 只能生成草稿，不能直接覆盖用户数据
5. **无持久化状态**：用户数据只存在 JSON 文件中，不存在前端或后端内存中（缓存除外）

## Non-Goals

- 不引入数据库（保持 JSON 文件系统）
- 不引入 WebSocket/SSE
- 不引入客户端状态管理库（使用 React useState/useReducer）
- 不重写 Storage 层
- 不做 PWA 或离线支持
- 不做多用户/权限系统
