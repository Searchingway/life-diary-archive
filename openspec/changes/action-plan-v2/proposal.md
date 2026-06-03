## Why

当前 ActionPlan 页面是普通 CRUD 表单，不符合执行工作台的定位。用户需要的不是填表，而是**查看今日任务、拖拽调整计划、可视化进度**。

V2 的目标：将 ActionPlan 页面改造为三视图执行工作台（Today View / Gantt View / Chain View），所有编辑操作通过弹窗完成，主页面用于浏览和执行。

## What Changes

- 重写 `diary_v2.0/Untitled/src/app/pages/ActionPlan.tsx`
- 新增 three-view 组件：
  - `TodayView.tsx` — 按日期分组的任务卡片
  - `GanttView.tsx` — 时间横轴甘特图
  - `ChainView.tsx` — 黑色背景任务链画布
- 新增弹窗组件：
  - `PlanEditDialog.tsx` — 新建/编辑计划
  - `TaskEditDialog.tsx` — 新建/编辑任务
- 新增 `useActionPlanReducer.ts` — 状态模型实现
- 新增 `useAIBreakdown.ts` — AI 拆解流程

## Capabilities

### New
- `action-plan-three-views`: Today / Gantt / Chain 三模式
- `action-plan-plan-dialog`: 弹窗式计划编辑
- `action-plan-task-dialog`: 弹窗式任务编辑
- `action-plan-gantt-drag`: 甘特图拖拽调整日期
- `action-plan-chain-drag`: 任务链节点拖拽
- `action-plan-ai-breakdown`: AI 拆解轻计划为任务

### Modified
- `action-plan-data-model`: ActionPlanTask 新增 x/y 可选坐标字段（已兼容旧数据）

## Impact

- `diary_v2.0/Untitled/src/app/pages/ActionPlan.tsx` — 从普通 CRUD 重写为三视图
- `diary_v2.0/Untitled/src/app/pages/` — 新增视图组件目录
- `src/life_dairy/action_plan_storage.py` — 已兼容 x/y 字段（无需改动）
- `openspec/specs/action-plan/spec.md` — 补充三视图需求
