## Context

当前 ActionPlan 页面把创建表单直接铺满主页面，不符合执行工作台的定位。用户使用场景是：

1. 早上打开 → 看今天要做什么（Today View）
2. 调整本周安排 → 拖拽甘特图（Gantt View）
3. 感受推进节奏 → 查看任务链（Chain View）
4. 晚上 → 勾选完成，写总结

## Goals / Non-Goals

**Goals:**
- 左侧保持计划列表（搜索 + 状态筛选 + 列表）
- 右侧按三种视图展示任务
- 新建/编辑计划使用弹窗
- Today View 按日期分组，标注"今天"和"逾期"
- Gantt View 时间横轴 + 任务条 + 可拖拽
- Chain View 深色背景 + 圆形节点 + 可拖动 + 坐标保存
- AI 拆解入口在头部按钮

**Non-Goals:**
- 不做任务间依赖线
- 不做日历整页模式
- 不做通知提醒
- 不做多选批量操作

## Layout

```
┌─────────────────────────────────────────────────────┐
│ 左侧(280px)              │ 右侧(980px)               │
│ ┌────────────────────┐  │ ┌──────────────────────┐  │
│ │ 搜索框               │  │ 标题 | 类型 | 状态 | 进度  │  │
│ │ 状态筛选              │  │ [编辑计划] [AI拆解]     │  │
│ │ ───────────────── │  │ ├──────────────────────┤  │
│ │ 计划列表              │  │ [时间表] [甘特图] [任务链] │  │
│ │ ├ Plan A ─── 50%  │  │ ├──────────────────────┤  │
│ │ ├ Plan B ─── 80%  │  │ │                      │  │
│ │ └ Plan C ─── 20%  │  │ │  视图内容区域            │  │
│ │                    │  │ │                      │  │
│ │ [新建] [删除]        │  │ │                      │  │
│ └────────────────────┘  │ └──────────────────────┘  │
│                         │ [添加任务] [编辑所选] [删除所选]│
└─────────────────────────────────────────────────────┘
```

## Component Tree

```
ActionPlanPage
├── Sidebar
│   ├── SearchBox
│   ├── StatusFilter
│   ├── PlanList
│   └── SidebarActions (新建/删除)
├── MainArea
│   ├── PlanHeader (标题/类型/状态/进度/编辑按钮/AI按钮)
│   ├── ViewTabs (时间表 | 甘特图 | 任务链)
│   ├── ViewContent
│   │   ├── TodayView
│   │   ├── GanttView
│   │   └── ChainView
│   └── TaskBar (添加/编辑/删除)
├── PlanEditDialog (弹窗)
├── TaskEditDialog (弹窗)
├── AIBreakdownDialog (弹窗)
└── AIPreviewDialog (弹窗)
```

## Data Flow

```
用户操作 → dispatch(event) → reducer(newState) → re-render
                              ↕ async
                          effect → API call → dispatch(SUCCESS/FAILED)
```

- 所有状态变更通过 reducer 集中管理
- Effect 不修改 state，通过事件返回
- 视图切换不触发 API 调用
- 坐标更新 debounce 500ms 后保存
