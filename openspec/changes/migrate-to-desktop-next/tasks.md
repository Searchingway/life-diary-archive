# 迁移任务 — Desktop Next

> 所有任务未完成。

## 1. OpenSpec 规格体系

- [ ] 1.1 确认 specs/ 目录文件完整（desktop-legacy、desktop-next、action-plan、ai-preview、data-contract）
- [ ] 1.2 确认 changes/ 目录文件完整（migrate-to-desktop-next、action-plan-v2）
- [ ] 1.3 确认 archive 中 reverse-date-order 未被修改

## 2. 前端基础设施

- [ ] 2.1 搭建 React 路由（react-router，路径 `/`、`/diary`、`/plans`、`/action-plans` 等）
- [ ] 2.2 实现 `api.ts` 客户端层（fetch GET/POST/PUT/DELETE）
- [ ] 2.3 实现通用 ErrorBoundary
- [ ] 2.4 实现通用 LoadingSpinner
- [ ] 2.5 实现通用 EmptyState
- [ ] 2.6 实现通用 ConfirmDialog（删除确认）
- [ ] 2.7 实现通用的 usePageReducer hook（封装 INIT_PAGE → LOAD_SUCCESS/LOAD_FAILED 模式）

## 3. 通用 AI 预览弹窗

- [ ] 3.1 实现 AIPreviewDialog 组件（只读文本 + 警告条 + 应用/取消按钮）
- [ ] 3.2 实现 useAIPreview hook（封装 AI 调用 → 预览 → 确认/取消流程）
- [ ] 3.3 处理非法 JSON 显示原始返回

## 4. 页面实现（按优先级）

- [ ] 4.1 Dashboard — 统计卡片 + 模块列表 + 时间线
- [ ] 4.2 Diary — CRUD + 图片管理
- [ ] 4.3 LightPlan — CRUD + AI 补全 + AI 拆解入口
- [ ] 4.4 ActionPlan — CRUD + three-view + AI 拆解（见 action-plan-v2/tasks.md）
- [ ] 4.5 LightThought — CRUD + 想法列表 + AI 整理
- [ ] 4.6 LightResource — CRUD + 资源项管理 + AI 评估
- [ ] 4.7 InfoMemo — CRUD + 类型联动状态
- [ ] 4.8 SelfObservation — CRUD + 情绪/强度筛选
- [ ] 4.9 LessonsReflection — CRUD + 图片管理
- [ ] 4.10 SelfAnalysis — CRUD + 12-section form
- [ ] 4.11 WorksReflection — CRUD + 作品类型筛选
- [ ] 4.12 DataManager — 健康检查 + 备份/恢复

## 5. 后端适配

- [ ] 5.1 确认 data_api.py 覆盖所有模块的 list/save/delete
- [ ] 5.2 确认 server.py 路由覆盖前端所有 API 调用
- [ ] 5.3 确认 export_service.py 导出功能可用
- [ ] 5.4 确认 migration 逻辑（旧 data/ 复制到新 data/）正常

## 6. 验证

- [ ] 6.1 每个页面手动验证 CRUD 正常
- [ ] 6.2 每个 AI 入口验证预览 + 确认 + 取消正常
- [ ] 6.3 非法 JSON 不崩溃
- [ ] 6.4 空数据引导不崩溃
- [ ] 6.5 软删除后列表不显示已删记录
