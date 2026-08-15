# 人生档案 Diary Desktop Next — 页面状态模型

> 本文档不描述技术实现，只描述每个页面的状态结构、事件驱动转移、派生状态、异步效应、不变约束和边界条件。
>
> 核心公式：`state + event → newState → view`

---

## 1. Dashboard / 总览

### 1.1 Page Goal

总览页不是简单的数据仪表盘，是用户打开软件后第一眼看到的工作台，回答"我现在在哪里、今天要做什么、最近发生了什么"。

### 1.2 State Shape

```typescript
// ── server state ──
interface DashboardServerState {
  modules: ModuleSummary[];         // 各模块名 + 记录数 + 最近更新时间
  recent: TimelineItem[];           // 最近 20 条跨模块记录
  stats: DashboardStats;            // 本月/今年日记数、字数、图片数、完成计划数、行动计划数、今日待办
}

// ── UI state ──
interface DashboardUIState {
  loading: boolean;
  error: string | null;
  lastRefreshedAt: string | null;   // ISO timestamp
}

// ── derived state ──
// todayPendingTasks: stats.today_pending_tasks
// inProgressActionPlans: stats.active_action_plan_count
```

### 1.3 Events

INIT_PAGE | REFRESH | LOAD_SUCCESS | LOAD_FAILED | CLICK_RECENT_ITEM

### 1.4 Transition Table

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| loading=true | LOAD_SUCCESS({stats, modules, recent}) | 无 | loading=false, server state 更新 | 显示统计数据、模块列表、时间线 |
| loading=true | LOAD_FAILED(error) | 无 | loading=false, error=msg | 显示错误提示，保留上次数据 |
| error=msg | REFRESH | 无 | loading=true, error=null | 显示刷新中 |
| 任意 | CLICK_RECENT_ITEM(id) | 无 | 通过 navigate event 跳转 | 跳转到对应模块的对应记录 |

### 1.5 Reducer Pseudocode

```
function dashboardReducer(state, event):
  switch event.type:
    case "INIT_PAGE":
      return { ...state, loading: true, error: null }
    case "LOAD_SUCCESS":
      return { ...state, loading: false, error: null, ...event.data }
    case "LOAD_FAILED":
      return { ...state, loading: false, error: event.message }
    case "REFRESH":
      return { ...state, loading: true, error: null }
    default:
      return state
```

### 1.6 Effects

- INIT_PAGE → fetch GET /api/overview → LOAD_SUCCESS | LOAD_FAILED
- REFRESH → fetch GET /api/overview → LOAD_SUCCESS | LOAD_FAILED

### 1.7 View Mapping

- loading=true → 骨架屏或 loading spinner
- error!=null → 错误提示条（可关闭），下方保留上次数据
- stats.month_diary_count → 本月日记篇数卡片
- stats.today_pending_tasks → 今日待办数字（若>0高亮显示）
- modules → 全模块数量列表
- recent → 按时间倒序的时间线列表
- CLICK_RECENT_ITEM → 对应模块的对应记录

### 1.8 Invariants

- recent 最多 20 条
- 时间线按 updated_at 降序
- 刷新时保留上次数据直到新数据到达

### 1.9 Edge Cases

- 全部模块无记录 → 显示空状态引导"新建第一篇日记"
- 网络/后端错误 → 显示"刷新失败"但不清空现有数据
- 今日待办数 = 0 → 不显示高亮，显示"今日暂无待办"
- 某模块数据目录不存在 → 该模块计数为 0，不崩溃

---

## 2. Diary / 日记

### 2.1 Page Goal

日记页是纯 CRUD 模块，用于按日期记录和浏览日记。核心操作是增删改查 + 图片管理。

### 2.2 State Shape

```typescript
// ── server state ──
interface DiaryEntry {
  id: string;
  title: string;
  body: string;
  date: string;           // "YYYY-MM-DD"
  images: DiaryImage[];
  createdAt: string;
  updatedAt: string;
}

interface DiaryServerState {
  entries: DiaryEntry[];
  currentEntry: DiaryEntry | null;  // 当前正在查看/编辑的完整记录
}

// ── draft state ──
interface DiaryDraft {
  title: string;
  body: string;
  date: string;
}

// ── UI state ──
interface DiaryUIState {
  loading: boolean;
  saving: boolean;
  error: string | null;
  query: string;
  selectedDate: string | null;       // 按日期筛选
  draft: DiaryDraft;
  isDirty: boolean;                  // draft != lastSaved
  imagePickerOpen: boolean;
}
```

### 2.3 Events

INIT_PAGE | LOAD_SUCCESS | LOAD_FAILED | SELECT_ENTRY | NEW_ENTRY | UPDATE_DRAFT | SAVE_REQUEST | SAVE_SUCCESS | SAVE_FAILED | DELETE_REQUEST | DELETE_SUCCESS | DELETE_FAILED | CHANGE_QUERY | CHANGE_DATE_FILTER | PICK_IMAGES | REMOVE_IMAGE | CLOSE_IMAGE_PICKER

### 2.4 Transition Table

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| entries=[], loading=false | INIT_PAGE | 无 | loading=true | 显示 loading |
| loading=true | LOAD_SUCCESS(entries) | 无 | entries=event.data, loading=false, select first | 列表填充，编辑区显示第一篇 |
| loading=true | LOAD_FAILED | 无 | loading=false, error=msg | 显示错误 |
| currentEntry=e, draft={t1,b1} | UPDATE_DRAFT({t2,b2}) | 无 | draft={t2,b2}, isDirty=true | 编辑区内容更新 |
| draft=d, isDirty=true | SAVE_REQUEST | 无 | saving=true | 保存按钮变禁用+加载 |
| saving=true | SAVE_SUCCESS(entry) | 无 | saving=false, currentEntry=entry, isDirty=false | 列表更新，编辑区刷新 |
| saving=true | SAVE_FAILED | 无 | saving=false, error=msg | 显示错误 |
| currentEntry=e | DELETE_REQUEST | isDirty=false | 显示确认弹窗 | — |
| 确认后 | DELETE_SUCCESS | 无 | currentEntry=next or null | 列表移除，编辑区清空 |
| 任意 | CHANGE_QUERY(q) | 无 | query=q | 列表重新过滤 |
| 任意 | SELECT_DATE(d) | 无 | selectedDate=d | 仅显示该日期日记 |

### 2.5 Reducer Pseudocode

```
function diaryReducer(state, event):
  switch event.type:
    case "INIT_PAGE":
      return { ...state, loading: true, error: null }
    case "LOAD_SUCCESS":
      return { ...state, loading: false, error: null, entries: event.entries }
    case "SELECT_ENTRY":
      entry = state.entries.find(e => e.id === event.id)
      return { ...state, currentEntry: entry, draft: { title: entry.title, body: entry.body, date: entry.date }, isDirty: false }
    case "NEW_ENTRY":
      return { ...state, currentEntry: null, draft: { title: "", body: "", date: today }, isDirty: false }
    case "UPDATE_DRAFT":
      return { ...state, draft: { ...state.draft, ...event.partial }, isDirty: true }
    case "SAVE_REQUEST":
      return { ...state, saving: true, error: null }
    case "SAVE_SUCCESS":
      return { ...state, saving: false, isDirty: false, currentEntry: event.entry, entries: replace(state.entries, event.entry) }
    case "SAVE_FAILED":
      return { ...state, saving: false, error: event.message }
    case "CHANGE_QUERY":
      return { ...state, query: event.query }
    case "DELETE_SUCCESS":
      next = state.entries.length > 1 ? state.entries.filter(e => e.id !== event.id)[0] : null
      return { ...state, currentEntry: next, entries: state.entries.filter(e => e.id !== event.id) }
    default: return state
```

### 2.6 Effects

- INIT_PAGE → fetch GET /api/modules/entries → LOAD_SUCCESS | LOAD_FAILED
- SAVE_REQUEST → PUT /api/modules/entries with draft → SAVE_SUCCESS | SAVE_FAILED
- DELETE_REQUEST → DELETE /api/modules/entries/:id → DELETE_SUCCESS | DELETE_FAILED

### 2.7 View Mapping

- entries filtered by query + selectedDate → 左侧列表
- currentEntry || draft → 右侧编辑区
- isDirty=true → 显示"未保存"标记，开启自动保存
- saving=true → 保存按钮禁用
- error != null → 顶部错误条

### 2.8 Invariants

- draft 必须和 currentEntry 分开存储，编辑过程中不修改 currentEntry
- 保存成功后才用返回的 entry 替换 currentEntry
- 切换条目时如果 isDirty=true 必须先保存或放弃

### 2.9 Edge Cases

- 空列表 → 显示"还没有日记，写第一篇"
- 查询无结果 → 显示"没有匹配的日记"
- 删除最后一条 → 清空编辑区
- 保存过程中切换条目 → 阻止切换或自动保存后切换

---

## 3. LightPlan / 轻计划

### 3.1 Page Goal

轻计划是快速记录"我想做什么"的入口，只有核心字段：标题、类型（加法/减法）、优先级、备注。不加复杂任务管理。

### 3.2 State Shape

```typescript
// ── server state ──
interface LightPlan {
  id: string;
  title: string;
  dueDate: string;
  status: "未开始" | "进行中" | "已完成" | "搁置";
  priority: "低" | "普通" | "高";
  planType: "add" | "subtract";
  notes: string;
  // 减法计划专属
  subtractMode?: "少做" | "不做" | "暂停" | "戒断";
  triggerScene?: string;
  avoidBehavior?: string;
  reason?: string;
  alternativeAction?: string;
  tags: string[];
}

// ── derived state ──
// isSubtract: planType === "subtract"
```

### 3.3 Events

INIT_PAGE | LOAD_SUCCESS | SELECT_PLAN | NEW_PLAN | UPDATE_DRAFT | SAVE_REQUEST | SAVE_SUCCESS | DELETE_REQUEST | DELETE_SUCCESS | CHANGE_QUERY | CHANGE_TYPE_FILTER | MARK_DONE | OPEN_AI_COMPLETE | RECEIVE_AI_DRAFT | APPLY_AI_DRAFT | CANCEL_AI_DRAFT | OPEN_AI_DECOMPOSE | RECEIVE_DECOMPOSE | APPLY_DECOMPOSE

### 3.4 Transition Table (核心事件)

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| 任意 | OPEN_AI_COMPLETE | AI enabled + key configured | aiLoading=true | 显示 AI 加载中 |
| aiLoading=true | RECEIVE_AI_DRAFT(draft) | 合法 JSON | aiLoading=false, aiDraft=draft, aiPreviewOpen=true | 弹出 AI 预览弹窗 |
| aiLoading=true | RECEIVE_AI_DRAFT(err) | 非法响应 | aiLoading=false, error=msg | 显示错误 |
| aiPreviewOpen=true, aiDraft=d | APPLY_AI_DRAFT | 用户点击应用 | aiPreviewOpen=false, draft={...d}, isDirty=true | 表单填入 AI 内容 |
| aiPreviewOpen=true, aiDraft=d | CANCEL_AI_DRAFT | 无 | aiPreviewOpen=false | 关弹窗，表单不变 |
| 任意 | OPEN_AI_DECOMPOSE | 有 selectedPlanId | decomposeDialogOpen=true | 弹出日期设置弹窗 |
| decomposeDialogOpen=true | RECEIVE_DECOMPOSE(result) | 合法 JSON | 创建 ActionPlan，跳转 | 跳转到行动计划页 |

### 3.5 Effects

- INIT_PAGE → fetch GET /api/modules/plans
- SAVE_REQUEST → PUT /api/modules/plans
- DELETE_REQUEST → DELETE /api/modules/plans
- OPEN_AI_COMPLETE → call AI api → RECEIVE_AI_DRAFT
- OPEN_AI_DECOMPOSE → call AI api → RECEIVE_DECOMPOSE
- MARK_DONE → PUT status="已完成"

### 3.6 View Mapping

- 左侧：搜索框 + 类型筛选(全部/加法/减法) + 列表
- 右侧：编辑表单 + 保存/完成/AI 按钮
- planType="subtract" → 显示减法计划专属字段
- aiPreviewOpen=true → 预览弹窗

### 3.7 Invariants

- AI 草稿不能直接覆盖 draft，必须先进入预览状态
- 减法计划的加法字段必须清空（已在存储层实施）
- 拆解为行动计划后不在本页做任何修改，跳转到 ActionPlan 页

---

## 4. ActionPlan / 行动计划 ⭐

### 4.1 Page Goal

行动计划页不是 CRUD 表单，是**执行工作台**。用户在这里：

1. 按日期查看今天要做什么（today 视图）
2. 按时间分布整体查看计划进度（gantt 视图）
3. 以任务链方式感知连续性和推进感（chain 视图）
4. 编辑计划基础信息（弹窗）
5. 管理子任务（CRUD + 勾选）
6. AI 拆解轻计划为结构化任务

### 4.2 State Shape

```typescript
// ── View enum ──
type ActionPlanView = "today" | "gantt" | "chain";

// ── server state ──
interface ActionPlanTask {
  id: string;
  title: string;
  date: string;                  // "YYYY-MM-DD"
  estimatedMinutes: number;
  done: boolean;
  note: string;
  x?: number | null;            // 任务链 x 坐标
  y?: number | null;            // 任务链 y 坐标
}

interface ActionPlan {
  id: string;
  title: string;
  planType: string;
  description: string;
  startDate: string;
  endDate: string;
  dailyAvailableTime: string;
  priority: "低" | "普通" | "高";
  status: "未开始" | "进行中" | "暂停" | "已完成" | "放弃";
  sourceLightPlanId: string;
  tasks: ActionPlanTask[];
  summary: string;
  createdAt: string;
  updatedAt: string;
}

interface ActionPlanServerState {
  plans: ActionPlan[];
}

// ── UI state ──
interface ActionPlanUIState {
  selectedPlanId: string | null;
  selectedTaskId: string | null;
  currentView: ActionPlanView;
  query: string;
  statusFilter: string;            // "全部" | ACTION_PLAN_STATUSES
  loading: boolean;
  saving: boolean;
  error: string | null;
  // 弹窗状态
  planEditorOpen: boolean;
  taskEditorOpen: boolean;
  aiBreakdownDialogOpen: boolean;
  aiPreviewOpen: boolean;
  deleteConfirmTarget: "plan" | "task" | null;
}

// ── draft state ──
interface ActionPlanDraft {
  title: string;
  planType: string;
  description: string;
  startDate: string;
  endDate: string;
  dailyAvailableTime: string;
  priority: string;
  status: string;
  summary: string;
}

interface TaskDraft {
  title: string;
  date: string;
  estimatedMinutes: number;
  note: string;
  done: boolean;
}

// ── AI draft state ──
interface AIDraft {
  title: string;
  planType: string;
  description: string;
  tasks: { date: string; title: string; estimatedMinutes: number; note: string }[];
  raw: string;       // 原始返回，用于非法 JSON 时展示
}

// ── derived state ──
// selectedPlan: plans.find(p => p.id === selectedPlanId)
// selectedTask: selectedPlan?.tasks.find(t => t.id === selectedTaskId)
// progress: selectedPlan ? doneCount / totalCount * 100 : 0
// todayTasks: selectedPlan?.tasks.filter(t => t.date === today && !t.done)
// groupedByDate: selectedPlan?.tasks.reduce((acc, t) => { acc[t.date] ??= []; acc[t.date].push(t); return acc }, {})
// overdueTasks: selectedPlan?.tasks.filter(t => t.date < today && !t.done)
// isDirty: draft != lastSavedPlan
// aiBreakdownParams: { startDate, endDate, dailyTime }
```

### 4.3 Events

```
// 初始化 & 数据加载
INIT_PAGE
LOAD_SUCCESS
LOAD_FAILED

// 计划列表
SELECT_PLAN
CHANGE_QUERY
CHANGE_STATUS_FILTER
NEW_PLAN
DELETE_PLAN_REQUEST
DELETE_PLAN_CONFIRM
DELETE_PLAN_SUCCESS
DELETE_PLAN_FAILED

// 视图切换
SWITCH_VIEW                  // payload: ActionPlanView

// 计划编辑
OPEN_PLAN_EDITOR
UPDATE_PLAN_DRAFT
SAVE_PLAN_REQUEST
SAVE_PLAN_SUCCESS
SAVE_PLAN_FAILED
CLOSE_PLAN_EDITOR

// 任务选择
SELECT_TASK
TOGGLE_TASK_DONE             // payload: taskId, done

// 任务编辑
OPEN_TASK_EDITOR             // payload: taskId | null (null = new)
UPDATE_TASK_DRAFT
SAVE_TASK_REQUEST
SAVE_TASK_SUCCESS
SAVE_TASK_FAILED
CLOSE_TASK_EDITOR
DELETE_TASK_REQUEST
DELETE_TASK_CONFIRM

// AI 拆解
OPEN_AI_BREAKDOWN
UPDATE_AI_BREAKDOWN_PARAMS
SUBMIT_AI_BREAKDOWN
AI_BREAKDOWN_LOADING
RECEIVE_AI_DRAFT
AI_BREAKDOWN_FAILED
CANCEL_AI_DRAFT
APPLY_AI_DRAFT

// 任务链坐标
UPDATE_TASK_POSITION         // payload: taskId, x, y
```

### 4.4 Transition Table

#### 初始化 & 列表

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| loading=false, plans=[] | INIT_PAGE | 无 | loading=true | 全页 loading |
| loading=true | LOAD_SUCCESS(plans) | plans.length>0 | plans=event.data, loading=false, selectedPlanId=plans[0].id | 列表填充，右侧显示第一个计划 |
| loading=true | LOAD_SUCCESS([]) | 空 | plans=[], loading=false | 显示空状态引导"新建行动计划" |
| loading=true | LOAD_FAILED | 无 | loading=false, error=msg | 错误提示 |

#### 计划选择

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlanId=p1 | SELECT_PLAN(p2) | p2!=p1 | selectedPlanId=p2, selectedTaskId=null, currentView="today" | 左侧高亮切换，右侧刷新为 p2 的 today 视图 |
| selectedPlanId=p1 | SELECT_PLAN(p1) | 重复点击 | 不变 | 无变化 |

#### 视图切换

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlanId!=null, currentView="today" | SWITCH_VIEW("gantt") | 当前计划存在 | currentView="gantt", selectedTaskId=null | 右侧从今日任务切换为甘特图 |
| selectedPlanId!=null, currentView="gantt" | SWITCH_VIEW("chain") | 当前计划存在 | currentView="chain" | 右侧切换为任务链 |
| selectedPlanId=null | SWITCH_VIEW(任意) | 无计划 | 不变，或 toast "请先选择计划" | 无变化 |

#### 任务勾选

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlan.tasks | TOGGLE_TASK_DONE(t, true) | 无 | tasks[t].done=true, 进度重新计算 | 任务样式变为已完成，进度条更新，今日待办-1 |
| selectedPlan.tasks | TOGGLE_TASK_DONE(t, false) | 无 | tasks[t].done=false, 进度重新计算 | 任务还原，进度条更新 |

#### 计划编辑（弹窗）

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| 任意 | OPEN_PLAN_EDITOR | selectedPlanId!=null | planEditorOpen=true, planDraft=selectedPlan | 弹出计划编辑弹窗 |
| planEditorOpen=true | UPDATE_PLAN_DRAFT | 无 | planDraft={...planDraft, ...event.partial} | 表单字段实时更新 |
| planEditorOpen=true | SAVE_PLAN_REQUEST | 无 | planEditorOpen=false, saving=true | 关闭弹窗，保存中 |
| saving=true | SAVE_PLAN_SUCCESS(plan) | 无 | saving=false, plans 替换对应项，selectedPlan 更新 | 列表和头部信息刷新 |
| saving=true | SAVE_PLAN_FAILED | 无 | saving=false, error=msg | 错误提示 |

#### 任务编辑

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| 任意 | OPEN_TASK_EDITOR(taskId) | selectedPlan!=null | taskEditorOpen=true, taskDraft=task | 弹出任务编辑弹窗 |
| 任意 | OPEN_TASK_EDITOR(null) | selectedPlan!=null | taskEditorOpen=true, taskDraft=empty(taskDraft) | 弹出新建任务弹窗（空表单） |
| taskEditorOpen=true | SAVE_TASK_REQUEST | 无 | taskEditorOpen=false | 关闭弹窗 |
| 后续 | SAVE_TASK_SUCCESS | 无 | tasks 更新或追加 | 列表/视图刷新 |
| 后续 | SAVE_TASK_FAILED | 无 | error=msg | 错误提示 |

#### AI 拆解

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| 任意 | OPEN_AI_BREAKDOWN | selectedPlan!=null | aiBreakdownDialogOpen=true | 弹出日期设置弹窗 |
| aiBreakdownDialogOpen=true | UPDATE_AI_BREAKDOWN_PARAMS({s,e,t}) | 无 | params 更新 | 表单更新 |
| aiBreakdownDialogOpen=true | SUBMIT_AI_BREAKDOWN | 日期合法 | aiBreakdownDialogOpen=false, aiLoading=true | 显示 AI 加载中 |
| aiLoading=true | RECEIVE_AI_DRAFT(draft) | 合法 JSON | aiLoading=false, aiDraft=draft, aiPreviewOpen=true | 弹出 AI 预览 |
| aiLoading=true | AI_BREAKDOWN_FAILED(msg) | 非法 JSON | aiLoading=false, error=msg, raw=msg | 显示错误 + 原始返回 |
| aiPreviewOpen=true, aiDraft=d | APPLY_AI_DRAFT | 用户确认 | aiPreviewOpen=false, tasks 替换为 d.tasks, saving=true | 保存后刷新视图 |
| aiPreviewOpen=true | CANCEL_AI_DRAFT | 无 | aiPreviewOpen=false | 关闭，无变化 |

#### 任务链坐标

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| currentView="chain" | UPDATE_TASK_POSITION(t,x,y) | 无 | tasks[t].x=x, tasks[t].y=y | 节点移动到新位置 |
| — | 自动保存 | 坐标变化 | 触发 SAVE_TASK_REQUEST | — |

### 4.5 Reducer Pseudocode

```
function actionPlanReducer(state, event):
  switch event.type:
    case "INIT_PAGE":
      return { ...state, loading: true, error: null }
    case "LOAD_SUCCESS":
      p = event.plans
      firstId = p.length > 0 ? p[0].id : null
      return { ...state, loading: false, plans: p, selectedPlanId: firstId }
    case "LOAD_FAILED":
      return { ...state, loading: false, error: event.message }
    case "SELECT_PLAN":
      if event.planId === state.selectedPlanId: return state
      return { ...state, selectedPlanId: event.planId, selectedTaskId: null, currentView: "today" }
    case "SWITCH_VIEW":
      return { ...state, currentView: event.view, selectedTaskId: null }
    case "TOGGLE_TASK_DONE":
      plan = state.plans.find(p => p.id === state.selectedPlanId)
      tasks = plan.tasks.map(t => t.id === event.taskId ? { ...t, done: event.done } : t)
      plans = state.plans.map(p => p.id === state.selectedPlanId ? { ...p, tasks } : p)
      return { ...state, plans }
    case "OPEN_PLAN_EDITOR":
      plan = state.plans.find(p => p.id === state.selectedPlanId)
      return { ...state, planEditorOpen: true, planDraft: toPlanDraft(plan) }
    case "UPDATE_PLAN_DRAFT":
      return { ...state, planDraft: { ...state.planDraft, ...event.partial } }
    case "SAVE_PLAN_REQUEST":
      return { ...state, planEditorOpen: false, saving: true }
    case "SAVE_PLAN_SUCCESS":
      plans = state.plans.map(p => p.id === event.plan.id ? event.plan : p)
      return { ...state, saving: false, plans }
    case "SAVE_PLAN_FAILED":
      return { ...state, saving: false, error: event.message }
    case "OPEN_TASK_EDITOR":
      task = event.taskId != null ? findTask(state, event.taskId) : emptyTaskDraft()
      return { ...state, taskEditorOpen: true, taskDraft: task }
    case "UPDATE_TASK_DRAFT":
      return { ...state, taskDraft: { ...state.taskDraft, ...event.partial } }
    case "SAVE_TASK_REQUEST":
      return { ...state, taskEditorOpen: false }
    case "SAVE_TASK_SUCCESS":
      // 替换或追加 task
      plan = state.plans.find(p => p.id === state.selectedPlanId)
      tasks = plan.tasks.some(t => t.id === event.task.id)
        ? plan.tasks.map(t => t.id === event.task.id ? event.task : t)
        : [...plan.tasks, event.task]
      plans = state.plans.map(p => p.id === state.selectedPlanId ? { ...p, tasks } : p)
      return { ...state, plans }
    case "UPDATE_TASK_POSITION":
      plan = state.plans.find(p => p.id === state.selectedPlanId)
      tasks = plan.tasks.map(t => t.id === event.taskId ? { ...t, x: event.x, y: event.y } : t)
      plans = state.plans.map(p => p.id === state.selectedPlanId ? { ...p, tasks } : p)
      return { ...state, plans }
    case "OPEN_AI_BREAKDOWN":
      return { ...state, aiBreakdownDialogOpen: true, aiBreakdownParams: { startDate: today, endDate: +7, dailyTime: "" } }
    case "SUBMIT_AI_BREAKDOWN":
      return { ...state, aiBreakdownDialogOpen: false, aiLoading: true }
    case "RECEIVE_AI_DRAFT":
      return { ...state, aiLoading: false, aiDraft: event.draft, aiPreviewOpen: true }
    case "AI_BREAKDOWN_FAILED":
      return { ...state, aiLoading: false, error: event.message, rawAIResponse: event.raw }
    case "APPLY_AI_DRAFT":
      // 用 aiDraft 替换当前计划的 title/planType/tasks
      plan = state.plans.find(p => p.id === state.selectedPlanId)
      newPlan = { ...plan, title: state.aiDraft.title, planType: state.aiDraft.planType, tasks: state.aiDraft.tasks }
      plans = state.plans.map(p => p.id === state.selectedPlanId ? newPlan : p)
      return { ...state, aiPreviewOpen: false, plans, aiDraft: null }
    case "CANCEL_AI_DRAFT":
      return { ...state, aiPreviewOpen: false, aiDraft: null }
    case "DELETE_TASK_CONFIRM":
      plan = state.plans.find(p => p.id === state.selectedPlanId)
      tasks = plan.tasks.filter(t => t.id !== event.taskId)
      plans = state.plans.map(p => p.id === state.selectedPlanId ? { ...p, tasks } : p)
      return { ...state, plans }
    default: return state
```

### 4.6 Effects

| Event | Effect | Result Event |
|---|---|---|
| INIT_PAGE | fetch GET /api/modules/action_plans | LOAD_SUCCESS | LOAD_FAILED |
| SAVE_PLAN_REQUEST | PUT /api/modules/action_plans with planDraft | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| TOGGLE_TASK_DONE | PUT /api/modules/action_plans with updated tasks | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| SAVE_TASK_REQUEST | PUT /api/modules/action_plans with updated tasks | SAVE_TASK_SUCCESS | SAVE_TASK_FAILED |
| DELETE_PLAN_CONFIRM | DELETE /api/modules/action_plans/:id | DELETE_PLAN_SUCCESS | DELETE_PLAN_FAILED |
| SUBMIT_AI_BREAKDOWN | call AI api with plan title + params | RECEIVE_AI_DRAFT | AI_BREAKDOWN_FAILED |
| APPLY_AI_DRAFT | PUT /api/modules/action_plans (save after AI apply) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| UPDATE_TASK_POSITION | debounce 500ms → PUT /api/modules/action_plans | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |

### 4.7 View Mapping

| State | View |
|---|---|
| loading=true | 全页骨架屏 |
| error!=null | 错误警示条（不阻隔内容） |
| plans.length=0 | 空状态插画 + "新建第一个行动计划" |
| selectedPlanId!=null | 右侧展示当前计划 |
| currentView="today" | 按日期分组的卡片列表，标注"今天"和"逾期" |
| currentView="gantt" | 时间横轴 + 任务条，按天分布 |
| currentView="chain" | 黑色背景 + 竖向节点链 |
| selectedTaskId!=null | 任务详情卡（在链模式下高亮节点） |
| planEditorOpen=true | 模态弹窗（标题/类型/描述/日期/优先级/状态/总结） |
| taskEditorOpen=true | 模态弹窗（标题/日期/耗时/备注/已完成） |
| aiBreakdownDialogOpen=true | 日期设置小弹窗 |
| aiPreviewOpen=true | AI 预览弹窗（只读 + 应用/取消按钮） |
| aiLoading=true | AI 加载指示器 |
| query | 筛选后的计划列表 |
| statusFilter | 筛选后的计划列表 |
| progress | 头部进度条 |
| overdueTasks.length>0 | 头部逾期警告 |

### 4.8 Invariants

- selectedTaskId 必须属于 selectedPlanId 对应的计划
- currentView 只能是 "today" | "gantt" | "chain"
- AI 结果不能直接写入正式数据，必须先进入 aiPreviewOpen 状态
- 删除记录必须先显示确认（deleteConfirmTarget）
- 任务完成状态变化后必须同步重新计算进度
- 弹窗关闭时如果存在未保存 draft，必须询问是否放弃
- 任务链坐标只应在 currentView="chain" 时可编辑
- 甘特图视图下任务应按 date 排序

### 4.9 Edge Cases

| 场景 | 处理 |
|---|---|
| 列表为空 | 显示空状态 + "新建行动计划"按钮 |
| 当前选中计划被其他操作删除 | 回退到 plans[0] 或 null |
| 后端加载失败 | 显示错误，保留上次数据 |
| AI 返回非法 JSON | 显示错误 + 原始返回文本，不崩溃 |
| 用户关闭编辑弹窗但有未保存 | 确认对话框"放弃修改？" |
| 甘特图任务没有 end_date | 任务条宽度按 estimatedMinutes 或显示为单点 |
| 任务链节点缺少 x/y | 自动按顺序垂直布局 |
| 导入旧数据缺少字段 | toDict/fromDict 提供默认值 |
| 空计划（0 个任务） | 显示"还没有任务"，进度 0% |
| 所有任务已完成 | 进度 100%，显示庆祝状态 |
| todayTasks 为空 | 显示"今天没有待办任务" |

---

## 5. LightThought / 轻思考

### 5.1 Page Goal

轻思考用于快速记录一个悬而未决的问题，以及对它的思考过程。核心是想法列表的追加和整理，AI 辅助梳理。

### 5.2 State Shape

```typescript
interface LightThought {
  id: string;
  title: string;
  description: string;
  type: string;
  status: "思考中" | "已有结论" | "已转计划" | "暂时搁置";
  ideas: { time: string; text: string }[];
  preliminaryConclusion: string;
  notes: string;
}

interface LightThoughtState {
  thoughts: LightThought[];
  selectedThoughtId: string | null;
  query: string;
  typeFilter: string;
  statusFilter: string;
  loading: boolean;
  error: string | null;
  isDirty: boolean;
  // AI
  aiOrganizeLoading: boolean;
  aiPreviewOpen: boolean;
  aiDraft: any | null;
}

// drafted state via _fill_form / _read_form pattern
```

### 5.3 Events

INIT_PAGE | LOAD_SUCCESS | SELECT | NEW | UPDATE_DRAFT | SAVE_REQUEST | SAVE_SUCCESS | DELETE | CHANGE_QUERY | CHANGE_TYPE_FILTER | CHANGE_STATUS_FILTER | ADD_IDEA | REMOVE_IDEA | OPEN_AI_ORGANIZE | RECEIVE_AI_ORGANIZE | AI_FAILED | APPLY_AI | CANCEL_AI | CONVERT_TO_PLAN

### 5.4 Effects

- INIT_PAGE → fetch GET /api/modules/thoughts
- SAVE_REQUEST → PUT /api/modules/thoughts
- OPEN_AI_ORGANIZE → call AI api → RECEIVE_AI_ORGANIZE | AI_FAILED
- CONVERT_TO_PLAN → PUT /api/modules/plans (create) + PUT /api/modules/thoughts (status update)

### 5.5 View Mapping

- 左侧：搜索 + 类型筛选 + 状态筛选 + 列表
- 右侧：编辑表单 + 想法列表 + 追加想法输入框
- status="已转计划" → 显示"已转为轻计划"标签
- aiPreviewOpen=true → 预览弹窗，展示 AI 生成的结构化思考

### 5.6 Invariants

- AI 整理结果可以追加到想法列表或填入结论，但不能覆盖已有想法
- 转计划后轻思考状态变为"已转计划"，不可逆

---

## 6. LightResource / 轻资源

### 6.1 Page Goal

轻资源用于评估一件事值不值得做。核心是资源项管理（时间/金钱/精力）和轮回测试。

### 6.2 State Shape

```typescript
interface ResourceItem {
  type: string;
  // type=时间: directTime, indirectTime, recoveryTime, timeBlockInterrupt
  // type=金钱: amount, cycle, direction
  value?: string;
  note?: string;
}

interface LightResource {
  id: string;
  title: string;
  description: string;
  type: string;
  status: "考虑中" | "已决定" | "已放弃" | "已完成";
  resourceItems: ResourceItem[];
  overallJudgement: string;
  subjectiveFeeling: string;
  recurrenceTest: { nextWeek: string; oneYear: string; repeatWillingness: string };
  notes: string;
}

interface LightResourceState {
  resources: LightResource[];
  selectedId: string | null;
  query: string;
  typeFilter: string;
  statusFilter: string;
  loading: boolean;
  error: string | null;
  selectedResourceItemIndex: number | null;  // 当前选中的资源项
  // AI
  aiEvaluateLoading: boolean;
  aiPreviewOpen: boolean;
  aiDraft: any | null;
}
```

### 6.3 Events

INIT_PAGE | LOAD_SUCCESS | SELECT | NEW | UPDATE_DRAFT | SAVE_REQUEST | SAVE_SUCCESS | DELETE | ADD_RESOURCE_ITEM | UPDATE_RESOURCE_ITEM | REMOVE_RESOURCE_ITEM | SELECT_RESOURCE_ITEM | OPEN_AI_EVALUATE | RECEIVE_AI_EVALUATE | AI_FAILED | APPLY_AI | CANCEL_AI | CONVERT_TO_PLAN | COPY_TO_LESSON

### 6.4 Effects

- INIT_PAGE → fetch GET /api/modules/resources
- OPEN_AI_EVALUATE → call AI api → RECEIVE_AI_EVALUATE | AI_FAILED

### 6.5 View Mapping

- 资源项列表 + 右侧编辑区（根据类型显示不同字段）
- 轮回测试：三个问题文本区
- AI 评估结果可填入总体判断和轮回测试

---

## 7. InfoMemo / 信息备忘

### 7.1 Page Goal

信息备忘用于快速记录碎片信息。类型联动状态：接单记录、网课资源、通用信息各有一套独立状态和字段。

### 7.2 State Shape

```typescript
type InfoMemoType = "接单记录" | "网课资源" | "通用信息";

interface InfoMemo {
  id: string;
  title: string;
  infoType: InfoMemoType;
  status: string;       // 根据 infoType 决定可选值
  priority: string;
  tags: string[];
  source: string;
  link: string;
  localPath: string;
  note: string;
  typeFields: Record<string, any>;  // 类型专属字段
}

interface InfoMemoState {
  memos: InfoMemo[];
  selectedId: string | null;
  query: string;
  typeFilter: InfoMemoType | "全部";
  statusFilter: string;
  loading: boolean;
  error: string | null;
}

// status 可选值根据 typeFilter 切换：
// 接单记录 → ["沟通中","已接单","进行中","待验收","已交付","已结款","已取消"]
// 网课资源 → ["想看","已收藏","学习中","暂停","已学完","放弃"]
// 通用信息 → ["未处理","已记录","处理中","已完成","已归档"]
```

### 7.3 Events

INIT_PAGE | LOAD_SUCCESS | SELECT | NEW | UPDATE_DRAFT | SAVE_REQUEST | SAVE_SUCCESS | DELETE | CHANGE_QUERY | CHANGE_TYPE_FILTER (triggers status filter reset)

### 7.4 View Mapping

- typeFilter 变化时 statusFilter 联动重置
- infoType 变化时表单切换专属字段区

---

## 8. SelfObservation / 自我观察

### 8.1 Page Goal

记录当下的情绪和身体感受。核心字段少，只有情绪、强度、触发场景。

### 8.2 State Shape

```typescript
interface SelfObservation {
  id: string;
  time: string;            // ISO datetime
  emotion: string;         // OBSERVATION_EMOTIONS
  intensity: number;       // 1-5
  trigger: string;
  bodySensation: string;
  need: string;            // OBSERVATION_NEEDS
  notes: string;
}

interface SelfObservationState {
  observations: SelfObservation[];
  selectedId: string | null;
  query: string;
  emotionFilter: string;
  intensityFilter: string;
  loading: boolean;
  error: string | null;
}
```

### 8.3 Events

INIT_PAGE | LOAD_SUCCESS | SELECT | NEW | UPDATE_DRAFT | SAVE_REQUEST | SAVE_SUCCESS | DELETE | CHANGE_QUERY | CHANGE_EMOTION_FILTER | CHANGE_INTENSITY_FILTER

---

## 9. LessonsReflection / 教训与反思

### 9.1 Page Goal

记录犯错经历 + 教训。区别于轻资源（评估值不值得做），教训是已经发生了的事。

### 9.2 State Shape

```typescript
interface Lesson {
  id: string;
  title: string;
  date: string;
  category: string;
  severity: string;
  event: string;
  judgment: string;
  result: string;
  mistake: string;
  rootCause: string;
  cost: string;
  nextAction: string;
  oneSentence: string;
  tags: string[];
  images: LessonImage[];
  relatedDiaries: { entryId: string; date: string; title: string }[];
}
```

### 9.3 Events

标准 CRUD + 关联日记 + 图片管理。无 AI 入口。

---

## 10. SelfAnalysis / 自我分析

### 10.1 Page Goal

结构化分析情绪和重复模式。比轻思考更深，包含 12 个结构化字段（触发事件 → 情绪 → 身体反应 → 表面欲望 → 真实恐惧 → 真实欲望 → 重复模式 → 防御方式 → 类似经历 → 洞察 → 下一步）。

### 10.2 State Shape

```typescript
interface SelfAnalysis {
  id: string;
  title: string;
  date: string;
  analysisType: string;        // SELF_ANALYSIS_TYPES
  triggerEvent: string;
  emotion: string;
  bodyReaction: string;
  surfaceWant: string;
  realFear: string;
  realWant: string;
  repeatedPattern: string;
  imaginedJudgment: string;
  defense: string;
  similarExperience: string;
  insight: string;
  nextAction: string;
  tags: string[];
  images: AnalysisImage[];
  relatedDiaries: RelatedDiary[];
  relatedLessons: RelatedLesson[];
}
```

### 10.3 Events

标准 CRUD + 关联管理。无 AI 入口（当前版本）。

---

## 11. WorksReflection / 作品感悟

### 11.1 Page Goal

记录对书籍/电影/游戏等作品的感受和思考。核心字段是各种维度评价（喜欢/不喜欢/触动/自我连接）。

### 11.2 State Shape

标准 CRUD。`workType` 决定字段显示（旧版书籍兼容到 workType="书籍"）。

---

## 12. DataManager / 数据管理

### 12.1 Page Goal

数据管理页不是"页面"而是操作面板：查看数据目录、运行健康检查、备份/恢复、导入/导出。

### 12.2 State Shape

```typescript
interface DataManagerState {
  dataRoot: string;
  moduleCounts: { module: string; count: number }[];
  healthCheckRunning: boolean;
  healthCheckResults: { level: string; message: string }[];
  // 操作状态
  backupRunning: boolean;
  restoreRunning: boolean;
  importRunning: boolean;
  exportRunning: boolean;
  error: string | null;
}
```

### 12.3 Events

REFRESH | RUN_HEALTH_CHECK | HEALTH_CHECK_RESULT | BACKUP_REQUEST | BACKUP_SUCCESS | BACKUP_FAILED | RESTORE_REQUEST | IMPORT_REQUEST | EXPORT_REQUEST | OPEN_AI_SETTINGS

### 12.4 View Mapping

- 操作按钮 + 数据目录路径显示
- 模块计数列表
- 健康检查输出区域（可滚动文本）

---

## 13. AISettings / AI 设置

### 13.1 Page Goal

配置 DeepSeek API 参数。不是页面而是弹窗/对话框。

### 13.2 State Shape

```typescript
interface AISettings {
  apiKey: string;
  baseUrl: string;
  model: string;
  enabled: boolean;
  timeoutSeconds: number;
}

interface AISettingsDialogState {
  settings: AISettings;
  testing: boolean;             // 测试连接中
  testResult: { ok: boolean; message: string } | null;
  saved: boolean;
}
```

### 13.3 Events

INIT | UPDATE_FIELD | TEST_CONNECTION | TEST_SUCCESS | TEST_FAILED | SAVE | CANCEL

### 13.4 Invariants

- API Key 默认密码模式显示
- 测试连接结果不影响已保存设置
- 取消不保存任何修改
- live_diary.log 不打印完整 API Key

### 13.5 Edge Cases

- 未配置 Key 时点击测试 → 显示"未配置 API Key"
- openai 库未安装 → 测试 AI 时提示安装，不阻止弹窗打开

---

## 14. AIPreviewDialog / AI 预览确认弹窗

### 14.1 Page Goal

AI 预览弹窗不是独立页面，是所有 AI 入口的共用确认层。核心原则：AI 只能生成草稿，不能直接覆盖用户数据。

### 14.2 State Shape

```typescript
// 每个调用 AI 的页面各自持有自己的 AIPreviewState
interface AIPreviewState {
  open: boolean;
  title: string;                // 弹窗标题
  content: string;              // 预览文本
  rawResponse: string;          // AI 原始返回（用于非法 JSON 展示）
  warning: string;              // "将覆盖当前字段"等
  loading: boolean;
  error: string | null;
  confirmed: boolean;           // 用户是否点击应用
}

// AI 调用的统一契约
interface AICallParams {
  systemPrompt: string;
  userPrompt: string;
  jsonMode: boolean;
}
```

### 14.3 Events

OPEN_PREVIEW(title, content, warning?) | CONFIRM | CANCEL | SHOW_ERROR | SHOW_RAW_RESPONSE

### 14.4 Transition Table

| Current State | Event | New State | View Update |
|---|---|---|---|
| — | OPEN_PREVIEW(t,c,w) | open=true, title=t, content=c, warning=w | 弹出模态弹窗 |
| open=true | CONFIRM | open=false, confirmed=true | 关闭弹窗，触发父页面的 APPLY_AI_DRAFT |
| open=true | CANCEL | open=false, confirmed=false | 关闭弹窗，无变化 |
| — | SHOW_ERROR(msg) | error=msg | 弹窗中显示错误 |
| — | SHOW_RAW_RESPONSE(raw) | content=raw | 显示 AI 原始返回文本 |

### 14.5 Invariants

- AI 结果必须预览，不能跳过
- 预览内容必须只读
- 警告文字在表单已有内容时必须显示
- confirmed=true 是父页面 APPLY 的唯一条件
- 非法 JSON 时显示原始返回 + 错误提示，不是崩溃

### 14.6 Edge Cases

- 用户关闭弹窗（X 按钮）→ 等同于 CANCEL
- AI 返回内容超长 → 弹窗应有滚动
- 多次快速连续调用 AI → 上一次的预览应被覆盖或取消
- 弹窗已打开时再次触发 AI 调用 → 先关闭再重新打开
> ARCHIVED / HISTORICAL DOCUMENT
> 不代表当前实现，请阅读 docs/CURRENT.md
