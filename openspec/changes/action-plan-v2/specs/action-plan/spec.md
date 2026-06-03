# Action Plan V2 — Change Delta Spec

> 此文件是 `openspec/specs/action-plan/spec.md` 的变更增量。
> 未列出的 Requirement 继承自主 spec。

## MODIFIED Requirements

### Requirement: Action Plan Task Model Supports Today, Gantt, and Chain Data

**R2**: ActionPlanTask 的数据模型从单日任务升级为三视图兼容模型。

#### Scenario: Task has both single-date and date-range fields

- GIVEN a task with `startDate="2026-06-01"` and `endDate="2026-06-05"`
- THEN the Gantt View SHALL render a task bar from Jun 1 to Jun 5
- AND the bar width SHALL be `(endDate - startDate + 1) days` = 5 days
- AND `estimatedMinutes` SHALL NOT affect the bar width

#### Scenario: Done task forces progress to 100

- GIVEN a task with `done=true`
- THEN `progress` SHALL always be `100`
- AND the reducer SHALL set `progress=100` when `TOGGLE_TASK_DONE(true)` fires
- AND the view SHALL render the task bar with 100% fill

#### Scenario: Legacy date-only task is compatible

- GIVEN old data with only `date="2026-06-01"` (no startDate/endDate/scheduledDate)
- THEN the system SHALL convert to `scheduledDate="2026-06-01"`, `startDate="2026-06-01"`, `endDate="2026-06-01"`
- AND the task SHALL render correctly in all three views

### Requirement: Action Plan Supports Three Execution Views

**R2**: 用户可以在三种视图间切换。

#### Scenario: Switch from Today to Gantt

- WHEN the user clicks the "Gantt" tab
- THEN `currentView` SHALL change to `"gantt"`
- AND the right panel SHALL show the gantt chart (task list on the left, date axis on the right)
- AND `selectedTaskId` SHALL be reset to `null`
- AND no API call SHALL be made

#### Scenario: Switch from Gantt to Chain

- WHEN the user clicks the "Chain" tab
- THEN `currentView` SHALL change to `"chain"`
- AND the right panel SHALL show the task chain canvas
- AND no API call SHALL be made

### Requirement: Gantt View Uses Date Ranges

**R2.2**: 甘特图基于 `startDate / endDate` 绘制任务条。

#### Scenario: Gantt renders task bars by date range

- GIVEN a plan with tasks that have startDate and endDate
- WHEN the user is on Gantt View
- THEN each task SHALL be rendered as a horizontal bar
- AND the bar left edge SHALL be at the column corresponding to `startDate`
- AND the bar width SHALL be `(endDate - startDate + 1) days`
- AND `progress` SHALL be shown as fill color inside the bar
- AND `estimatedMinutes` SHALL NOT affect bar width

#### Scenario: User moves task bar in Gantt View

- WHEN the user drags a task bar to a later date range
- THEN `startDate` and `endDate` SHALL both shift by the same number of days
- AND `estimatedMinutes` SHALL remain unchanged
- AND `dependsOn` SHALL remain unchanged
- AND `chainX` / `chainY` SHALL remain unchanged

#### Scenario: User resizes task bar from left edge

- WHEN the user drags the left edge of a task bar to an earlier date
- THEN only `startDate` SHALL change to the new date
- AND `endDate` SHALL remain unchanged
- AND the operation SHALL be blocked if `newStartDate > endDate`

#### Scenario: User resizes task bar from right edge

- WHEN the user drags the right edge of a task bar to a later date
- THEN only `endDate` SHALL change to the new date
- AND `startDate` SHALL remain unchanged
- AND the operation SHALL be blocked if `newEndDate < startDate`

### Requirement: Chain View Supports Dependency and Node Layout

**R2.3**: 任务链展示任务的推进关系和依赖。

#### Scenario: Chain shows dependency lines

- GIVEN task A has `dependsOn: ["taskB"]`
- WHEN the user is on Chain View
- THEN there SHALL be a line from task B's node to task A's node
- AND the arrow direction SHALL indicate dependency (B → A)

#### Scenario: No dependency data auto-lays out by date

- GIVEN tasks have no `dependsOn` values
- WHEN the user is on Chain View
- THEN tasks SHALL be automatically positioned by `startDate` / `scheduledDate` / creation order
- AND tasks on the same date SHALL share a column

#### Scenario: User drags a node only changes coordinates

- WHEN the user drags a task node to a new position
- THEN only `chainX` and `chainY` SHALL change
- AND `startDate` / `endDate` / `dependsOn` SHALL remain unchanged

#### Scenario: Deleting a task cleans up dependsOn references

- GIVEN task A has `dependsOn: ["taskB"]`
- WHEN task B is deleted
- THEN task A's `dependsOn` SHALL be `[]`
- AND the chain view SHALL remove the line to task B

#### Scenario: Circular dependency is detected and blocked

- GIVEN task A depends on task B, and task B depends on task A
- WHEN the user tries to set `dependsOn: ["taskA"]` for task B
- THEN the operation SHALL be blocked
- AND the user SHALL see an error message "存在循环依赖"

### Requirement: AI Breakdown Uses Preview-Confirm-Apply Flow

**R5**: AI 拆解使用预览-确认-应用流程。

#### Scenario: AI returns tasks with complete fields

- WHEN the AI responds with tasks
- THEN each task SHALL include `startDate`, `endDate`, `progress`, `scheduledDate`, `dependsOn`
- AND if AI only returns `date` (legacy format), the system SHALL convert to `scheduledDate=date`, `startDate=date`, `endDate=date`

#### Scenario: User confirms AI draft

- WHEN the user clicks "应用" in AIPreviewDialog
- THEN the current plan's `title`, `planType`, and `tasks` SHALL be replaced with the AI draft
- AND the plan SHALL be saved to the backend
- AND the view SHALL switch to today view

#### Scenario: User cancels AI draft

- WHEN the user clicks "取消" in AIPreviewDialog
- THEN the AI draft SHALL be discarded
- AND the current plan SHALL remain unchanged
- AND no API call SHALL be made

## UNCHANGED Requirements

The following requirements from `openspec/specs/action-plan/spec.md` are unchanged and apply to V2:

- R1: Action Plan List（列表 CRUD 不变）
- R2.1: Today View（按 scheduledDate 分组，其余行为不变）
- R3: Task CRUD（新增 scheduledDate/startDate/endDate/dependsOn/chainX/chainY 字段）
- R4: Plan CRUD（不变）

## DELETED Requirements

- Non-Goals 中的"不做任务依赖关系" — V2 新增 `dependsOn`
- "不做甘特图的依赖线绘制" — V2 Chain View 使用 dependsOn 绘制连线
