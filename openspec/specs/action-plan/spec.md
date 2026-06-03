# Action Plan — 系统规格

> 状态：**设计中**

## Overview

行动计划是轻计划的执行层。轻计划回答"我想做什么"，行动计划回答"我什么时候做、做到哪了"。一个行动计划包含一组子任务，支持 Today / Gantt / Chain 三种执行视图。

## Data Model

```typescript
interface ActionPlan {
  id: string;
  title: string;
  planType: string;              // 学习 | 接单 | 项目 | 生活 | 身体 | 武术 | 情绪 | 长期目标 | 其他
  description: string;
  startDate: string;             // "YYYY-MM-DD"
  endDate: string;
  dailyAvailableTime: string;
  priority: string;              // 低 | 普通 | 高
  status: string;                // 未开始 | 进行中 | 暂停 | 已完成 | 放弃
  sourceLightPlanId: string;     // 来源轻计划 ID（可为空）
  tasks: ActionPlanTask[];
  summary: string;
  createdAt: string;
  updatedAt: string;
}

interface ActionPlanTask {
  id: string;
  title: string;

  // Today View：今日任务 / 简单日程
  scheduledDate?: string;          // "YYYY-MM-DD"，用于 today 视图，可为空

  // Gantt View：真正的甘特图
  startDate: string;               // "YYYY-MM-DD"
  endDate: string;                 // "YYYY-MM-DD"
  progress: number;                // 0-100，甘特图内部进度填充

  // Chain View：任务链 / 依赖关系
  dependsOn: string[];             // 前置任务 id 列表
  chainX?: number | null;          // 任务链节点 x 坐标
  chainY?: number | null;          // 任务链节点 y 坐标

  // 通用信息
  estimatedMinutes: number;        // 仅显示信息，不决定甘特图条宽
  done: boolean;                   // done=true 时 progress=100
  status: "todo" | "doing" | "done" | "blocked";
  note: string;
}
```

### 字段解释

| 字段 | 用途 |
|------|------|
| `scheduledDate` | 用于 Today View 按日显示，可为空 |
| `startDate / endDate` | 用于 Gantt View，决定任务条位置（startDate）和宽度（endDate - startDate + 1天） |
| `progress` | 甘特图任务条内部进度填充，取值 0-100 |
| `dependsOn` | 用于 Chain View 生成任务连线，也用于未来依赖关系检验 |
| `chainX / chainY` | 任务链节点坐标，无值时自动布局 |
| `estimatedMinutes` | 仅限 tooltip / 详情显示，不参与甘特图条宽计算 |
| `done` | 完成标记，done=true 时 progress 必须为 100 |

## Storage

- 路径：`data/Diary/action_plans/<uuid>/action_plan.json`
- 使用 `ActionPlanStorage`（`src/life_dairy/action_plan_storage.py`）
- 软删除：与所有模块一致

## Requirement: Action Plan List

**R1**: 用户可以看到全部行动计划的列表。
- Scenario: 打开 ActionPlan 页面，左侧显示计划列表，每个条目显示标题、类型、状态、进度百分比。
- Scenario: 空数据时显示空状态引导。
- Scenario: 搜索按标题/描述/任务匹配。
- Scenario: 可按状态筛选（全部/未开始/进行中/暂停/已完成/放弃）。

## Requirement: Three Views

**R2**: 用户可以在三种视图间切换查看当前计划的子任务。

### R2.1 Today View（时间表）

- Scenario: 子任务按 `scheduledDate` 分组显示。无 `scheduledDate` 的任务归入"未安排"组。
- Scenario: 每个任务显示标题、预计耗时、备注。
- Scenario: 可勾选完成。勾选后 `done=true`、`progress=100`，进度条更新。
- Scenario: 已完成任务有明确视觉区分（删除线或颜色淡化）。
- Scenario: 日期分组标注"今天"和"逾期"。
- Scenario: 逾期任务（`scheduledDate < today && !done`）有警告标识。

### R2.2 Gantt View（甘特图）

- Scenario: 左侧是任务列表，右侧是日期横轴（从计划 startDate 到 endDate）。
- Scenario: 每个任务是一条横向任务条。
- Scenario: 任务条左边界位置由 `startDate` 决定。
- Scenario: 任务条宽度由 `endDate - startDate + 1 天` 决定。
- Scenario: `progress` 显示为任务条内部的进度填充色。
- Scenario: `estimatedMinutes` 只显示在 tooltip 中，不参与条宽计算。
- Scenario: 已完成任务颜色变灰。
- Scenario: 拖动任务条整体时，同时偏移 `startDate` 和 `endDate`，天数跨度不变。
- Scenario: 拖动任务条左边缘时只修改 `startDate`。
- Scenario: 拖动任务条右边缘时只修改 `endDate`。
- Scenario: `startDate` 不能晚于 `endDate`。
- Scenario: 任务超出当前时间窗口时支持水平滚动。

### R2.3 Chain View（任务链）

- Scenario: 深色背景画布。
- Scenario: 优先使用 `dependsOn` 生成任务间连接线。
- Scenario: 无 `dependsOn` 时按 `startDate / scheduledDate / 创建顺序` 自动排列。
- Scenario: 每个任务是一个可拖动的圆形节点。
- Scenario: 节点位置优先使用 `chainX / chainY`，无坐标时自动布局。
- Scenario: 已完成节点亮绿色，未完成蓝色渐变。
- Scenario: 悬停显示任务信息（标题/日期/耗时/状态/备注）。
- Scenario: 双击节点打开任务编辑弹窗。
- Scenario: 拖动节点只改变 `chainX / chainY`，不改变 `startDate / endDate`。
- Scenario: 删除任务时清理其他任务的 `dependsOn` 引用。
- Scenario: `dependsOn` 不能形成循环依赖。

## Requirement: Task CRUD

**R3**: 用户可以在当前计划下管理子任务。
- Scenario: 添加任务（弹窗输入标题/日期范围/耗时/备注/前置任务）。
- Scenario: 编辑任务（弹窗）。
- Scenario: 删除任务（确认后删除，同时清理其他任务的 dependsOn）。
- Scenario: 勾选完成。
- Scenario: 批量操作非必需。

## Requirement: Plan CRUD

**R4**: 用户可以对行动计划本身做 CRUD。
- Scenario: 新建计划（弹窗输入标题/类型/描述/日期/优先级等）。
- Scenario: 编辑计划（弹窗）。
- Scenario: 删除计划（确认后软删除）。

## Requirement: AI Breakdown

**R5**: 用户可以从轻计划使用 AI 拆解为行动计划。
- Scenario: 在轻计划页点击"AI 拆解为行动计划"。
- Scenario: 弹窗输入开始日期/截止日期/每日可用时间。
- Scenario: AI 返回的任务必须包含 `startDate / endDate / progress / scheduledDate / dependsOn`。
- Scenario: 如果 AI 只返回 `date`（旧格式），兼容转换为 `scheduledDate = date`、`startDate = date`、`endDate = date`。
- Scenario: 显示 AI 预览弹窗。
- Scenario: 用户确认后创建行动计划。
- Scenario: 非法 JSON 时显示错误 + 原始返回。

## Non-Goals

- 不做日历视图
- 不做任务提醒/通知
- 不做多用户协作
- `estimatedMinutes` 不参与甘特图条宽计算（仅显示信息）
