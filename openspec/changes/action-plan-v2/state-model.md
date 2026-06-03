# ActionPlan V2 — 状态模型

> 核心公式：`state + event → newState → view`

## State Shape

```typescript
// ── View enum ──
type ActionPlanView = "today" | "gantt" | "chain";

// ── Server State ── （来自后端 API）
interface ActionPlanTask {
  id: string;
  title: string;

  // Today View：今日任务 / 简单日程
  scheduledDate?: string;          // "YYYY-MM-DD"，可为空

  // Gantt View：真正的甘特图
  startDate: string;               // "YYYY-MM-DD"
  endDate: string;                 // "YYYY-MM-DD"
  progress: number;                // 0-100

  // Chain View：任务链 / 依赖关系
  dependsOn: string[];             // 前置任务 id 列表
  chainX: number | null;           // 任务链节点坐标
  chainY: number | null;

  // 通用信息
  estimatedMinutes: number;
  done: boolean;                   // done=true 时 progress=100
  status: "todo" | "doing" | "done" | "blocked";
  note: string;
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

// ── UI State ──
interface ActionPlanState {
  // 列表
  plans: ActionPlan[];
  selectedPlanId: string | null;
  query: string;
  statusFilter: string;
  loading: boolean;
  saving: boolean;
  error: string | null;

  // 视图
  currentView: ActionPlanView;

  // 任务选择
  selectedTaskId: string | null;

  // 弹窗
  planEditorOpen: boolean;
  taskEditorOpen: boolean;
  deleteConfirmTarget: { type: "plan" | "task"; id: string } | null;

  // AI 拆解
  aiBreakdownDialogOpen: boolean;
  aiBreakdownParams: { startDate: string; endDate: string; dailyTime: string };
  aiLoading: boolean;
  aiDraft: ActionPlan | null;
  aiPreviewOpen: boolean;
  aiRawResponse: string | null;
}

// ── Derived State ──
// selectedPlan:        plans.find(p => p.id === selectedPlanId)
// selectedTask:        selectedPlan?.tasks.find(t => t.id === selectedTaskId)
// progress:            doneCount / totalCount * 100
// todayTasks:          selectedPlan?.tasks where scheduledDate === today && !done
// overdueTasks:        selectedPlan?.tasks where scheduledDate < today && !done
// hasCycleDependency:  detectCycle(selectedPlan?.tasks)
```

## Events

```typescript
type ActionPlanEvent =
  // 初始化 & 加载
  | { type: "INIT_PAGE" }
  | { type: "LOAD_SUCCESS"; plans: ActionPlan[] }
  | { type: "LOAD_FAILED"; message: string }

  // 列表
  | { type: "SELECT_PLAN"; planId: string }
  | { type: "CHANGE_QUERY"; query: string }
  | { type: "CHANGE_STATUS_FILTER"; filter: string }
  | { type: "NEW_PLAN" }
  | { type: "DELETE_PLAN_REQUEST"; planId: string }
  | { type: "DELETE_PLAN_CONFIRM" }
  | { type: "DELETE_PLAN_CANCEL" }
  | { type: "DELETE_PLAN_SUCCESS"; planId: string }
  | { type: "DELETE_PLAN_FAILED"; message: string }

  // 视图
  | { type: "SWITCH_VIEW"; view: ActionPlanView }

  // 计划编辑
  | { type: "OPEN_PLAN_EDITOR" }
  | { type: "CLOSE_PLAN_EDITOR" }
  | { type: "SAVE_PLAN_REQUEST"; plan: Partial<ActionPlan> }
  | { type: "SAVE_PLAN_SUCCESS"; plan: ActionPlan }
  | { type: "SAVE_PLAN_FAILED"; message: string }

  // 任务选择 & 勾选
  | { type: "SELECT_TASK"; taskId: string | null }
  | { type: "TOGGLE_TASK_DONE"; taskId: string; done: boolean }

  // 任务编辑
  | { type: "OPEN_TASK_EDITOR"; taskId: string | null }
  | { type: "CLOSE_TASK_EDITOR" }
  | { type: "SAVE_TASK_REQUEST"; task: Partial<ActionPlanTask> }
  | { type: "SAVE_TASK_SUCCESS"; task: ActionPlanTask }
  | { type: "SAVE_TASK_FAILED"; message: string }
  | { type: "DELETE_TASK_REQUEST"; taskId: string }
  | { type: "DELETE_TASK_CONFIRM" }
  | { type: "DELETE_TASK_CANCEL" }

  // 甘特图拖拽
  | { type: "MOVE_TASK_ON_GANTT"; taskId: string; newStartDate: string; newEndDate: string }
  | { type: "RESIZE_TASK_ON_GANTT"; taskId: string; edge: "left" | "right"; newDate: string }

  // 任务链拖拽 & 依赖
  | { type: "MOVE_NODE_ON_CHAIN"; taskId: string; chainX: number; chainY: number }
  | { type: "UPDATE_TASK_DEPENDENCY"; taskId: string; dependsOn: string[] }

  // AI 拆解
  | { type: "OPEN_AI_BREAKDOWN" }
  | { type: "CLOSE_AI_BREAKDOWN" }
  | { type: "UPDATE_AI_BREAKDOWN_PARAMS"; params: Partial<{ startDate: string; endDate: string; dailyTime: string }> }
  | { type: "SUBMIT_AI_BREAKDOWN" }
  | { type: "RECEIVE_AI_DRAFT"; draft: ActionPlan; raw: string }
  | { type: "AI_RESPONSE_INVALID"; raw: string; message: string }
  | { type: "AI_FAILED"; message: string }
  | { type: "APPLY_AI_DRAFT" }
  | { type: "CANCEL_AI_DRAFT" };
```

## Transition Table

### 初始化 & 加载

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| loading=false | INIT_PAGE | 无 | loading=true, error=null | 全页 loading spinner |
| loading=true | LOAD_SUCCESS(plans) | plans.length>0 | plans=event.plans, loading=false, selectedPlanId=plans[0].id | 左侧列表填充，右侧显示第一个计划的 today 视图 |
| loading=true | LOAD_SUCCESS([]) | 空 | plans=[], loading=false, selectedPlanId=null | 空状态引导 |
| loading=true | LOAD_FAILED(msg) | 无 | loading=false, error=msg | 错误提示，不阻隔页面 |

### 列表操作

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlanId=p1 | SELECT_PLAN(p2) | p2 ≠ p1 | selectedPlanId=p2, selectedTaskId=null, currentView="today" | 左侧高亮切换，右侧刷新为 p2 |
| selectedPlanId=p1 | SELECT_PLAN(p1) | 无变化 | 不变 | 无反应 |
| selectedPlanId≠null | DELETE_PLAN_REQUEST(id) | 无 | deleteConfirmTarget={type:"plan", id} | 显示删除确认弹窗 |
| deleteConfirmTarget≠null | DELETE_PLAN_CONFIRM | 无 | deleteConfirmTarget=null, saving=true | 执行删除 |
| saving=true | DELETE_PLAN_SUCCESS(id) | id===selectedPlanId | selectedPlanId=plans[0]?.id||null | 列表移除，右侧切换 |
| saving=true | DELETE_PLAN_FAILED(msg) | 无 | saving=false, error=msg | 错误提示 |

### 视图切换

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlanId≠null, currentView="today" | SWITCH_VIEW("gantt") | 无 | currentView="gantt", selectedTaskId=null | 右侧从时间表切换为甘特图（左侧任务列表 + 日期横轴 + 任务条） |
| selectedPlanId≠null, currentView="gantt" | SWITCH_VIEW("chain") | 无 | currentView="chain" | 右侧从甘特图切换为任务链（深色画布 + 圆形节点 + 依赖连线） |
| selectedPlanId=null | SWITCH_VIEW(任意) | 无 | 不变 | toast "请先选择计划" |

### 任务勾选

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlan.tasks[t] | TOGGLE_TASK_DONE(t, true) | 无 | tasks[t].done=true, tasks[t].progress=100, saving=true | 任务样式变灰，进度条增加 |
| saving=true | SAVE_PLAN_SUCCESS | 无 | saving=false | 保存成功 |
| 同上 | TOGGLE_TASK_DONE(t, false) | 无 | tasks[t].done=false, tasks[t].progress=0, saving=true | 任务还原 |

### 甘特图整体拖动

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| currentView="gantt" | MOVE_TASK_ON_GANTT(t, newStart, newEnd) | newStart <= newEnd | tasks[t].startDate=newStart, tasks[t].endDate=newEnd | 任务条整体移动到新日期范围 |
| — | (debounce 500ms) | 无 | saving=true → SAVE_PLAN_SUCCESS | 自动保存 |
| currentView="gantt" | MOVE_TASK_ON_GANTT(t, newStart, newEnd) | newStart > newEnd | 不变 + error | 不允许，显示 "开始日期不能晚于结束日期" |

### 甘特图边缘拖动

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| currentView="gantt" | RESIZE_TASK_ON_GANTT(t, "left", d) | d <= tasks[t].endDate | tasks[t].startDate=d | 左边缘移动到 d |
| currentView="gantt" | RESIZE_TASK_ON_GANTT(t, "right", d) | d >= tasks[t].startDate | tasks[t].endDate=d | 右边缘移动到 d |
| — | (debounce 500ms) | 无 | saving=true → SAVE_PLAN_SUCCESS | 自动保存 |

### 任务链拖拽

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| currentView="chain" | MOVE_NODE_ON_CHAIN(t, x, y) | 无 | tasks[t].chainX=x, tasks[t].chainY=y | 节点移动到新位置，连线重绘 |
| — | (debounce 500ms) | 无 | saving=true → SAVE_PLAN_SUCCESS | 坐标自动保存 |

### 任务依赖

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlanId≠null | UPDATE_TASK_DEPENDENCY(t, deps) | 无循环依赖 | tasks[t].dependsOn=deps | Chain View 连线更新 |
| selectedPlanId≠null | UPDATE_TASK_DEPENDENCY(t, deps) | 形成循环依赖 | 不变 + error="存在循环依赖" | 显示错误，不应用 |
| selectedPlanId≠null | DELETE_TASK_CONFIRM | 无 | 被删任务 id 从所有其他任务的 dependsOn 中移除 | 列表移除，依赖线清理 |

### AI 拆解

| Current State | Event | Condition | New State | View Update |
|---|---|---|---|---|
| selectedPlanId≠null | OPEN_AI_BREAKDOWN | 无 | aiBreakdownDialogOpen=true | 弹出时间设置弹窗 |
| aiBreakdownDialogOpen=true | SUBMIT_AI_BREAKDOWN | 日期合法 | aiBreakdownDialogOpen=false, aiLoading=true | 显示 AI 加载中 |
| aiLoading=true | RECEIVE_AI_DRAFT(draft, raw) | JSON 合法 | aiLoading=false, aiDraft=draft, aiPreviewOpen=true | 弹出 AI 预览弹窗 |
| aiLoading=true | AI_RESPONSE_INVALID(raw, msg) | 非法 JSON | aiLoading=false, error=msg, aiRawResponse=raw | 显示错误 + 原始返回 |
| aiLoading=true | AI_FAILED(msg) | 无 | aiLoading=false, error=msg | 显示错误 |
| aiPreviewOpen=true | APPLY_AI_DRAFT | 无 | aiPreviewOpen=false, aiDraft=null, plans 替换 tasks | 视图更新为新任务列表 |
| aiPreviewOpen=true | CANCEL_AI_DRAFT | 无 | aiPreviewOpen=false, aiDraft=null | 关闭，无变化 |

## Reducer Pseudocode

```typescript
function actionPlanReducer(state: ActionPlanState, event: ActionPlanEvent): ActionPlanState {
  switch (event.type) {
    case "INIT_PAGE":
      return { ...state, loading: true, error: null };

    case "LOAD_SUCCESS":
      const plans = event.plans;
      return {
        ...state, loading: false, error: null, plans,
        selectedPlanId: plans.length > 0 ? plans[0].id : null,
        currentView: "today", selectedTaskId: null,
      };

    case "LOAD_FAILED":
      return { ...state, loading: false, error: event.message };

    case "SELECT_PLAN":
      if (event.planId === state.selectedPlanId) return state;
      return { ...state, selectedPlanId: event.planId, selectedTaskId: null, currentView: "today" };

    case "NEW_PLAN":
      return { ...state, planEditorOpen: true };

    case "DELETE_PLAN_REQUEST":
      return { ...state, deleteConfirmTarget: { type: "plan", id: event.planId } };

    case "DELETE_PLAN_CONFIRM":
      return { ...state, deleteConfirmTarget: null, saving: true };

    case "DELETE_PLAN_SUCCESS": {
      const remaining = state.plans.filter(p => p.id !== event.planId);
      return { ...state, saving: false, plans: remaining,
        selectedPlanId: remaining.length > 0 ? remaining[0].id : null,
        selectedTaskId: null, currentView: "today" };
    }

    case "DELETE_PLAN_FAILED":
      return { ...state, saving: false, error: event.message };

    case "SWITCH_VIEW":
      if (state.selectedPlanId === null) return state;
      return { ...state, currentView: event.view, selectedTaskId: null };

    case "SAVE_PLAN_REQUEST":
      return { ...state, planEditorOpen: false, saving: true };

    case "SAVE_PLAN_SUCCESS": {
      const i = state.plans.findIndex(p => p.id === event.plan.id);
      const plans = i >= 0
        ? state.plans.map((p, idx) => idx === i ? event.plan : p)
        : [...state.plans, event.plan];
      return { ...state, saving: false, plans, selectedPlanId: event.plan.id };
    }

    case "SAVE_PLAN_FAILED":
      return { ...state, saving: false, error: event.message };

    case "SELECT_TASK":
      return { ...state, selectedTaskId: event.taskId };

    case "TOGGLE_TASK_DONE": {
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan) return state;
      const tasks = plan.tasks.map(t =>
        t.id === event.taskId
          ? { ...t, done: event.done, progress: event.done ? 100 : 0 }
          : t
      );
      return updateTasks(state, tasks);
    }

    case "OPEN_TASK_EDITOR":
      return { ...state, taskEditorOpen: true };

    case "CLOSE_TASK_EDITOR":
      return { ...state, taskEditorOpen: false };

    case "SAVE_TASK_REQUEST":
      return { ...state, taskEditorOpen: false, saving: true };

    case "SAVE_TASK_SUCCESS": {
      const p = state.plans.find(p => p.id === state.selectedPlanId);
      if (!p) return { ...state, saving: false };
      const existing = p.tasks.some(t => t.id === event.task.id);
      const tasks = existing
        ? p.tasks.map(t => t.id === event.task.id ? event.task : t)
        : [...p.tasks, event.task];
      return { ...updateTasks(state, tasks), saving: false };
    }

    case "SAVE_TASK_FAILED":
      return { ...state, saving: false, error: event.message };

    case "DELETE_TASK_REQUEST":
      return { ...state, deleteConfirmTarget: { type: "task", id: event.taskId } };

    case "DELETE_TASK_CONFIRM": {
      if (!state.deleteConfirmTarget) return state;
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan) return { ...state, deleteConfirmTarget: null };
      const removedId = state.deleteConfirmTarget.id;
      const tasks = plan.tasks
        .filter(t => t.id !== removedId)
        .map(t => ({ ...t, dependsOn: t.dependsOn.filter(d => d !== removedId) }));
      return { ...updateTasks(state, tasks), deleteConfirmTarget: null, selectedTaskId: null };
    }

    case "DELETE_TASK_CANCEL":
      return { ...state, deleteConfirmTarget: null };

    // 甘特图整体拖动：同时移动 startDate 和 endDate
    case "MOVE_TASK_ON_GANTT": {
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan || event.newStartDate > event.newEndDate) return state;
      const tasks = plan.tasks.map(t =>
        t.id === event.taskId
          ? { ...t, startDate: event.newStartDate, endDate: event.newEndDate }
          : t
      );
      return updateTasks(state, tasks);
    }

    // 甘特图边缘拖动：只改 startDate 或 endDate
    case "RESIZE_TASK_ON_GANTT": {
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan) return state;
      const task = plan.tasks.find(t => t.id === event.taskId);
      if (!task) return state;
      if (event.edge === "left" && event.newDate > task.endDate) return state;
      if (event.edge === "right" && event.newDate < task.startDate) return state;
      const tasks = plan.tasks.map(t =>
        t.id === event.taskId
          ? event.edge === "left"
            ? { ...t, startDate: event.newDate }
            : { ...t, endDate: event.newDate }
          : t
      );
      return updateTasks(state, tasks);
    }

    // 任务链拖拽：只改坐标
    case "MOVE_NODE_ON_CHAIN": {
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan) return state;
      const tasks = plan.tasks.map(t =>
        t.id === event.taskId
          ? { ...t, chainX: event.chainX, chainY: event.chainY }
          : t
      );
      return updateTasks(state, tasks);
    }

    // 任务依赖
    case "UPDATE_TASK_DEPENDENCY": {
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan) return state;
      if (hasCycle(plan.tasks, event.taskId, event.dependsOn)) {
        return { ...state, error: "存在循环依赖，无法设置" };
      }
      const tasks = plan.tasks.map(t =>
        t.id === event.taskId ? { ...t, dependsOn: event.dependsOn } : t
      );
      return updateTasks(state, tasks);
    }

    // AI 拆解
    case "OPEN_AI_BREAKDOWN":
      return { ...state, aiBreakdownDialogOpen: true, aiBreakdownParams: { startDate: todayISO(), endDate: addDays(todayISO(), 7), dailyTime: "" } };

    case "CLOSE_AI_BREAKDOWN":
      return { ...state, aiBreakdownDialogOpen: false };

    case "UPDATE_AI_BREAKDOWN_PARAMS":
      return { ...state, aiBreakdownParams: { ...state.aiBreakdownParams, ...event.params } };

    case "SUBMIT_AI_BREAKDOWN":
      return { ...state, aiBreakdownDialogOpen: false, aiLoading: true };

    case "RECEIVE_AI_DRAFT":
      return { ...state, aiLoading: false, aiDraft: event.draft, aiRawResponse: null, aiPreviewOpen: true };

    case "AI_RESPONSE_INVALID":
      return { ...state, aiLoading: false, error: event.message, aiRawResponse: event.raw, aiPreviewOpen: true };

    case "AI_FAILED":
      return { ...state, aiLoading: false, error: event.message };

    case "APPLY_AI_DRAFT": {
      if (!state.aiDraft || !state.selectedPlanId) return state;
      const plan = state.plans.find(p => p.id === state.selectedPlanId);
      if (!plan) return { ...state, aiPreviewOpen: false, aiDraft: null };
      const newPlan = { ...plan, title: state.aiDraft.title, planType: state.aiDraft.planType, tasks: state.aiDraft.tasks };
      return { ...state, aiPreviewOpen: false, aiDraft: null, plans: state.plans.map(p => p.id === state.selectedPlanId ? newPlan : p), selectedTaskId: null, currentView: "today" };
    }

    case "CANCEL_AI_DRAFT":
      return { ...state, aiPreviewOpen: false, aiDraft: null, aiRawResponse: null };

    default:
      return state;
  }
}

function updateTasks(state: ActionPlanState, tasks: ActionPlanTask[]): ActionPlanState {
  return { ...state, plans: state.plans.map(p => p.id === state.selectedPlanId ? { ...p, tasks } : p), saving: true };
}

function hasCycle(tasks: ActionPlanTask[], taskId: string, dependsOn: string[]): boolean {
  // 检测：为 taskId 设置 dependsOn 后是否产生循环依赖
  const visited = new Set<string>();
  const stack = [...dependsOn];
  while (stack.length > 0) {
    const id = stack.pop()!;
    if (id === taskId) return true;
    if (visited.has(id)) continue;
    visited.add(id);
    const task = tasks.find(t => t.id === id);
    if (task) stack.push(...task.dependsOn);
  }
  return false;
}
```

## Effects

| Trigger Event | Effect | Success Event | Failure Event |
|---|---|---|---|
| INIT_PAGE | fetch GET /api/modules/action_plans | LOAD_SUCCESS | LOAD_FAILED |
| SAVE_PLAN_REQUEST | PUT /api/modules/action_plans | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| DELETE_PLAN_CONFIRM | DELETE /api/modules/action_plans/:id | DELETE_PLAN_SUCCESS | DELETE_PLAN_FAILED |
| TOGGLE_TASK_DONE | PUT /api/modules/action_plans (tasks update) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| SAVE_TASK_REQUEST | PUT /api/modules/action_plans (tasks update) | SAVE_TASK_SUCCESS | SAVE_TASK_FAILED |
| DELETE_TASK_CONFIRM | PUT /api/modules/action_plans (tasks filter + cleanup dependsOn) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| MOVE_TASK_ON_GANTT | debounce 500ms → PUT (startDate/endDate update) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| RESIZE_TASK_ON_GANTT | debounce 500ms → PUT (startDate or endDate update) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| MOVE_NODE_ON_CHAIN | debounce 500ms → PUT (chainX/chainY update) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| UPDATE_TASK_DEPENDENCY | PUT /api/modules/action_plans (dependsOn update) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |
| SUBMIT_AI_BREAKDOWN | POST to AI backend /api/ai/breakdown | RECEIVE_AI_DRAFT | AI_FAILED |
| APPLY_AI_DRAFT | PUT /api/modules/action_plans (full after apply) | SAVE_PLAN_SUCCESS | SAVE_PLAN_FAILED |

## View Mapping

| State Condition | View Behavior |
|---|---|
| loading=true | 全页居中 loading spinner |
| loading=false, plans.length=0, error=null | 空状态插画 + "新建第一个行动计划" |
| error!=null | 顶部错误条（可关闭） |
| selectedPlanId=null | 右侧显示"请从左侧选择一个行动计划" |
| selectedPlanId≠null | 右侧头部显示标题/类型/状态/进度条 |
| currentView="today" | 任务按 scheduledDate 分组展示 |
| currentView="gantt" | 左侧任务列表 + 右侧日期横轴 + 任务条（位置=startDate，宽度=endDate-startDate+1天，填充=progress） |
| currentView="chain" | 深色背景画布 + 圆形节点（位置=chainX/chainY，连线=dependsOn） |
| selectedTaskId≠null + currentView="chain" | 对应节点高亮边框 |
| planEditorOpen=true | 模态弹窗 |
| taskEditorOpen=true | 模态弹窗 |
| deleteConfirmTarget≠null | 删除确认弹窗 |
| aiBreakdownDialogOpen=true | 日期设置小弹窗 |
| aiLoading=true | AI 加载指示器 |
| aiPreviewOpen=true | AI 预览弹窗 |
| aiRawResponse!=null | 预览弹窗显示原始返回 |
| selectedPlan.tasks.length=0 | "还没有任务" |
| overdueTasks.length>0 | 头部逾期警告 |
| progress=100 && tasks.length>0 | 进度条"全部完成" |

## Invariants

1. `currentView` 只能是 `"today" | "gantt" | "chain"` 三者之一。
2. `selectedTaskId` 必须属于 `selectedPlanId` 对应的计划。计划被删除时 selectedTaskId 置 null。
3. `startDate <= endDate`，任何时候不能违反。违反时拖动/边缘操作被阻止。
4. `progress` 必须在 0 到 100 之间。`done=true` 时 `progress=100`。
5. `dependsOn` 不能形成循环依赖。设置依赖时必须检测。
6. 删除任务时必须清理其他任务中的 `dependsOn` 引用。
7. 任务链拖动只改变 `chainX / chainY`，不改变 `startDate / endDate`。
8. 甘特图整体拖动同时改变 `startDate` 和 `endDate`，天数跨度不变。
9. 甘特图边缘拖动只改变对应侧的日期，不改变另一侧。
10. `estimatedMinutes` 不参与甘特图条宽计算，仅显示信息。
11. AI 草稿（aiDraft）不能直接写入 plans，必须先进入 `aiPreviewOpen` 状态。
12. 视图切换不触发 API 调用。
13. `saving=true` 时所有操作按钮禁用。

## Edge Cases

| 场景 | 处理 |
|---|---|
| 列表为空 | 空状态 + "新建"按钮 |
| 当前选中计划被删除 | 回退到 plans[0] 或 null |
| 后端加载失败 | 显示错误，保留上次数据 |
| AI 返回非法 JSON | 显示错误 + 原始返回 |
| 旧数据无 startDate/endDate | startDate=endDate=scheduledDate 或最初版本中的 date |
| 旧数据无 chainX/chainY | 按 date 和索引自动布局 |
| 任务链节点拖出可视区 | 限制 scene rect 或允许滚动 |
| 甘特图 startDate > endDate | 阻止操作并提示 |
| dependsOn 形成循环 | 检测并阻止，显示错误 |
| 被依赖的任务被删除 | 自动从 dependsOn 移除引用 |
| 计划有 0 个任务 | 进度 0%，显示 "还没有任务" |
| 所有任务已完成 | 进度 100%，进度条"全部完成！" |
| 今日待办为 0 | "今天没有待办任务" |
| 快速连续切换视图 | 纯状态切换，无 API 调用 |
