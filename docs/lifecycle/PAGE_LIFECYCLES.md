# Page Lifecycle Models

> 本文档定义每个页面的生命周期。通用生命周期引用 `COMMON_LIFECYCLE.md`，专有生命周期在此定义。

---

## 1. Dashboard / 总览

### Page Goal

总览页展示跨模块统计和时间线，不涉及数据编辑。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**：INIT_PAGE → fetch /api/overview → LOAD_SUCCESS | LOAD_FAILED
- **Record Selection Lifecycle**：仅限于时间线条目（NoSelection → RecordSelected 跳转到对应页面）

### Page-specific Lifecycles

Dashboard 无专用生命周期。它的生命周期等价于 Page Loading Lifecycle。

### Forbidden Transitions

- 不允许在 Dashboard 直接编辑或删除数据（只能跳转）
- 不允许 Dashboard 发起写入 API

### Implementation Notes

- 只需在 mount 时 INIT_PAGE 一次
- REFRESH 后显示刷新指示，但不清空旧数据
- 点击时间线条目后 navigate 到对应页面

---

## 2. Diary / 日记

### Page Goal

日记页是写作页面，不是 CRUD 列表。核心是写作流畅性 + 自动保存安全。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**（按日期选择日记）
- **Draft Editing Lifecycle**（正文/标题/日期编辑）
- **Auto Save Lifecycle**（写作时自动保存）
- **Delete Lifecycle**
- **Attachment / Image Lifecycle**

### Page-specific Lifecycles

#### Writing Lifecycle

写作状态转移的特殊规则：

```
Writing: DraftEditing + AutoSave 的复合状态
用户输入 → DirtyWaiting → (debounce) → AutoSaving → AutoSaved
手动保存 → SAVE_REQUEST → Saving → Saved
```

- 用户停止输入 3 秒后自动保存
- 手动保存优先级高于自动保存
- 切换日期时如果 Dirty，先执行一次手动保存

#### Export Lifecycle

适用于 Word/PDF/TXT 导出。使用通用 Export Lifecycle（`COMMON_LIFECYCLE.md` 第 8 节）。

### Forbidden Transitions

- 禁止热力图、图片区、导出按钮抢占正文主状态
- 禁止自动保存失败时清空正文
- 禁止切换记录时静默丢失 Dirty draft
- 禁止在非 Ready 状态下打开编辑
- 禁止 Dirty 状态切换日期时只弹一次确认——必须提供"保存并切换"、"放弃修改并切换"、"取消切换"三个选项

### Diary Switching Rules

Dirty 状态切换日期时，必须弹出选择：

- **保存并切换**：先执行一次手动保存，保存成功后切换
- **放弃修改并切换**：丢弃 draft，切换到目标日期
- **取消切换**：停留在当前日记

如果保存失败，必须停留在当前日记，不允许切换。

### Implementation Notes

- 图片上传使用 Attachment / Image Lifecycle，区分于正文编辑
- 自动保存失败不应阻塞用户继续写作
- 导出使用通用 Export Lifecycle

---

## 3. Footprints / 足迹

### Page Goal

足迹包含地点 + 多次访问 + 图片。层级比日记复杂。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**（地点列表选择）
- **Draft Editing Lifecycle**（地点信息 + 访问记录）
- **Delete Lifecycle**
- **Attachment / Image Lifecycle**

### Page-specific Lifecycles

#### Visit Selection Lifecycle

```
NoVisitSelected → VisitSelected
```

选中地点后，下方显示访问记录列表。每条访问包含日期、感想、图片。

#### Visit Editing Lifecycle

与 Draft Editing 相同，但适用于嵌套的访问记录。

### Forbidden Transitions

- 不能在没有选中地点时编辑访问记录
- 删除地点时不能静默删除下属访问记录（必须软删除全部）

### Implementation Notes

- 分为两层选中：地点 + 访问记录
- 地点列表是主要选中源（通用 Record Selection）
- 访问记录是次要选中源（页面专用）

---

## 4. LightPlan / 轻计划

### Page Goal

快速记录"我想做什么"的入口，不做复杂任务管理。区分加法计划和减法计划。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Delete Lifecycle**
- **AI Preview Lifecycle**（AI 补全计划）

### Page-specific Lifecycles

#### Additive Plan Lifecycle

加法计划的编辑生命周期 = 通用 Draft Editing。

#### Subtractive Plan Lifecycle

减法计划包含减法专属字段（triggerScene, avoidBehavior, reason, alternativeAction）。

当 `planType="subtract"` 时：
- 减法专属字段加入 draft
- 保存时加法字段自动清空

#### Convert to ActionPlan Lifecycle

轻计划提升为行动计划：

```
Idle → Converting → Converted (跳转到 ActionPlan 页)
          ↓
     ConvertFailed
```

- 转换后**不删除**原轻计划
- 转换后用户跳转到新建的行动计划

### Forbidden Transitions

- 轻计划不能直接变成复杂项目管理的 CRUD
- AI 结果不能直接写入计划，必须经过 AI Preview Lifecycle
- 转行动计划后**不能自动删除**轻计划

### Implementation Notes

- 减法计划字段默认收起，仅当 `planType="subtract"` 时展开
- AI 补全计划的入口按钮在编辑区上方
- "转行动计划"按钮触发 Convert to ActionPlan

---

## 5. ActionPlan / 行动计划

### Page Goal

ActionPlan 是执行工作台，不是 CRUD 表单。此处仅摘要，详见专项文件。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**（计划列表选择）
- **Delete Lifecycle**

### Page-specific Lifecycles

ActionPlan 有独立的完整生命周期文件：

```
openspec/changes/action-plan-v2/lifecycle.md
```

摘要：

| 生命周期 | 状态数 | 关键约束 |
|---------|--------|---------|
| **Today View Lifecycle** | 按 scheduledDate 分组 | 逾期任务警告 |
| **Gantt Task Lifecycle** | startDate/endDate 决定条宽 | estimatedMinutes 不参与 |
| **Chain Node Lifecycle** | 坐标和依赖分离 | 拖动只改坐标 |
| **AI Breakdown Lifecycle** | Previewing 是强制过渡 | 非法 JSON 不崩溃 |

### Forbidden Transitions

- 禁止把 ActionPlan 做成大表单（编辑必须进弹窗）
- 禁止甘特图任务条宽度使用 estimatedMinutes
- 禁止 AI 草稿跳过 Previewing 直接写入
- 禁止链节点拖拽改变 startDate/endDate

### Implementation Notes

- **实现前必须读取** `openspec/changes/action-plan-v2/lifecycle.md`
- 如果本文档与 ActionPlan 专项 lifecycle 冲突，**以专项文件为准**
- 三种视图切换不触发 API

---

## 6. LightThought / 轻思考

### Page Goal

记录悬而未决的问题和思考过程。核心是想法列表的追加和整理。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**（基本字段 + 想法列表）
- **Delete Lifecycle**
- **AI Preview Lifecycle**（AI 整理思考）

### Page-specific Lifecycles

#### Idea Appending Lifecycle

Idea Appending Lifecycle 是独立写入生命周期，不进入整个表单 Dirty 状态。

```
Idle → EditingIdea → AddIdeaRequest → AddIdeaSuccess → Idle（清空输入框）
                           ↓
                    AddIdeaFailed → Idle（保留输入框内容）
```

| State | 含义 |
|-------|------|
| Idle | 未编辑想法 |
| EditingIdea | 用户正在输入想法文本 |
| AddIdeaRequest | 正在向后端写入想法 |
| AddIdeaSuccess | 写入成功，追加到 ideas[] |
| AddIdeaFailed | 写入失败 |

**Rules：**

- 追加想法是**独立操作**，不影响整个表单的 Dirty 状态
- 点击追加后立即调用保存接口或局部更新接口
- 追加失败时保留输入框内容，用户可以重试
- 追加成功后清空输入框，想法追加到 ideas[]

#### Convert to Plan Lifecycle

与 LightPlan 的 Convert to ActionPlan 类似，但转为轻计划。

### Forbidden Transitions

- AI 整理结果不能覆盖已有想法列表（只追加）
- 切换记录时如果想法列表有未追加文本，提示保存

### Implementation Notes

- 想法列表是追加模式，不是编辑模式
- AI 整理的结果可以追加到想法列表或填入初步结论
- 转计划后轻思考状态变为"已转计划"

---

## 7. LightResource / 轻资源

### Page Goal

评估一件事值不值得做。核心是资源项管理和轮回测试。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Delete Lifecycle**
- **AI Preview Lifecycle**（AI 评估资源）

### Page-specific Lifecycles

#### Resource Item Editing Lifecycle

资源项是列表结构（resourceItems[]）：

```
Idle → AddingItem → ItemAdded → Idle
  ↑                    ↓
  │              继续添加
  ↓
Idle → EditingItem → ItemUpdated → Idle
```

- 添加资源项时先选择类型（时间/金钱/精力...）
- 不同类型显示不同字段
- 更新资源项时预填当前值

### Forbidden Transitions

- AI 评估结果不能直接覆盖已有字段
- AI 默认只填空白字段
- 如果 AI 草稿将覆盖已有字段，必须在 AIPreviewDialog 中显示覆盖警告
- 只有用户确认 Apply 后才能覆盖
- Cancel 不改变任何数据
- 轮回测试字段（nextWeek/oneYear/repeatWillingness）不共享状态

### Implementation Notes

- 资源项类型联动表单字段（选择"时间"显示时间字段，选择"金钱"显示金额）
- AI 评估结果可以填入总体判断和轮回测试

---

## 8. InfoMemo / 信息备忘

### Page Goal

记录碎片信息。类型联动状态：接单记录、网课资源、通用信息各有一套独立状态。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Delete Lifecycle**

### Page-specific Lifecycles

#### Type Switching Lifecycle

```
InfoType_Selected → Switch_Type → Update_Status_Filter → Update_Editor_Fields
```

- 切换 `infoType` 时，status 下拉选项联动变化
- 如果当前 status 不在新类型的可选列表中，重置为 DEFAULT_STATUS
- 类型专属字段通过 QStackedWidget（或 React 条件渲染）切换

#### Status Filter Lifecycle

```
AllStatuses → SelectType → FilterByType → ResetStatusFilter
```

- 类型筛选变化时，状态筛选自动联动
- 通用信息类型默认状态"未处理"
- 接单记录默认状态"沟通中"
- 网课资源默认状态"想看"

### Forbidden Transitions

- 主页面不能直接变成大表单（必须左侧列表 + 右侧详情/弹窗）
- 切换 infoType 后不能保留不合法 status
- 金额字段（报价/定金/尾款）不能互相覆盖

### Implementation Notes

- 接单记录有金额字段（price, deposit, final_payment），不能共用值
- 网课资源有 course_url 字段
- 通用信息有 category 字段

---

## 9. SelfObservation / 自我观察

### Page Goal

记录当下情绪和身体感受。字段少，结构简单。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Delete Lifecycle**

### Page-specific Lifecycles

无专用生命周期。值对象模式：情绪/强度/需求是固定枚举，不需要复杂编辑。

### Forbidden Transitions

- 情绪和强度是独立筛选，不联动

### Implementation Notes

- 情绪选择使用 enum，强度使用 1-5 slider
- 筛选按 emotion + intensity 独立进行

---

## 10. LessonsReflection / 教训与反思

### Page Goal

记录犯错经历和教训。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Delete Lifecycle**
- **Attachment / Image Lifecycle**

### Page-specific Lifecycles

无专用生命周期。所有编辑行为由通用生命周期覆盖。

### Forbidden Transitions

- 严重程度（轻微/中等/重要/严重）不联动其他字段

### Implementation Notes

- 事件类别和严重程度是独立枚举
- 图片管理与日记共用 Attachment / Image Lifecycle

---

## 11. SelfAnalysis / 自我分析

### Page Goal

结构化分析情绪和重复模式，包含 12 个字段。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Auto Save Lifecycle**（长文本）
- **Delete Lifecycle**
- **Attachment / Image Lifecycle**

### Page-specific Lifecycles

无专用生命周期。12 个字段都在同一 form 中，由 Draft Editing + Auto Save 覆盖。

### Forbidden Transitions

- 不允许部分字段进入 draft 而部分不进入（所有字段同时保存）
- 自动保存不能只保存部分字段

### Implementation Notes

- 12 个字段不多，不需要分步编辑
- Auto Save 适用于长文本字段（triggerEvent, insight 等）
- 所有字段存在同一个 JSON 的 sections 中

---

## 12. WorksReflection / 作品感悟

### Page Goal

记录对作品（书籍/电影/游戏等）的感受。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**
- **Record Selection Lifecycle**
- **Draft Editing Lifecycle**
- **Auto Save Lifecycle**
- **Delete Lifecycle**
- **Attachment / Image Lifecycle**

### Page-specific Lifecycles

无专用生命周期。

### Forbidden Transitions

- workType 变化不清空其他字段（兼容旧版 book 数据）

### Implementation Notes

- workType="书籍"时兼容旧版 book 数据
- 所有评价字段（liked/disliked/touched/selfConnection）是独立 text

---

## 13. DataManager / 数据管理

### Page Goal

数据管理页不是"页面"而是操作面板。不涉及通用 CRUD 生命周期。

### Applicable Common Lifecycles

- **Page Loading Lifecycle**（仅限于模块计数 + 路径显示）
- **Export Lifecycle**（数据导出、模块导出）

### Page-specific Lifecycles

#### Backup Lifecycle

```
Idle → BackingUp → BackupComplete → Idle
          ↓
     BackupFailed
```

- 备份前不需要确认（非破坏性操作）
- 备份完成后显示路径

#### Restore Lifecycle

```
Idle → ConfirmRestore → Restoring → RestoreComplete → 重载页面
          ↓                ↓
     CancelRestore     RestoreFailed
```

- restore 前**必须确认**
- restore 前**自动备份当前数据**
- restore 完成后重载全部页面

#### Import ZIP Lifecycle

与 Restore Lifecycle 相同（确认 → 自动备份 → 导入 → 重载）。

#### Health Check Lifecycle

```
Idle → RunningCheck → CheckComplete → Idle
```

- 健康检查是只读操作
- 检查结果只显示，不存储

### Forbidden Transitions

- 禁止在没有备份的情况下执行 restore/import
- 禁止 restore/import 失败后清空当前数据
- 禁止直接操作真实数据用于测试

### Implementation Notes

- destructive operation（restore/import）必须确认
- 失败后保留原数据不变
- 备份操作是安全操作，不需要确认

---

## 14. AISettings / AI 设置

### Page Goal

配置 DeepSeek API 参数。不是页面，是弹窗。

### Applicable Common Lifecycles

不适用通用生命周期。

### Page-specific Lifecycles

#### Settings Draft Lifecycle

```
LoadSettings → EditingSettings → SaveSettings → SettingsSaved
                                    ↓
                               SettingsFailed
```

- 加载配置填入表单
- 编辑不触发自动保存
- 只有点击"确定"才保存

#### Test Connection Lifecycle

```
Idle → Testing → TestSuccess (显示模型返回)
          ↓
     TestFailed (显示错误)
```

- 测试连接**不等于保存**
- 测试失败不能覆盖已保存配置

#### Save Settings Lifecycle

```
SettingsDraft → SaveRequest → Saving → Saved
                         ↓
                    SaveFailed (保留 draft)
```

### Forbidden Transitions

- API Key 输入框默认密码模式（不可见）
- 测试连接不能改变已保存的配置
- 日志不得打印完整 API Key

### Implementation Notes

- 弹窗打开前从后端加载当前设置
- 取消关闭弹窗不保存任何修改
- 保存后通知后端更新配置

---

## 15. AIPreviewDialog / AI 预览弹窗

### Page Goal

AI 预览弹窗不是独立页面，是共用确认层，所有 AI 入口必须经过它。

### Applicable Common Lifecycles

- **AI Preview Lifecycle**（已完整覆盖）

### Page-specific Lifecycles

AI 预览弹窗的生命周期 = AI Preview Lifecycle（`COMMON_LIFECYCLE.md` 第 7 节）。

无额外专用生命周期。

### Forbidden Transitions

- 禁止跳过 Previewing 状态直接写入
- 禁止 AI 预览弹窗自己写入 server state（只发事件给父页面）
- 禁止 AI 预览弹窗变成聊天窗口

### Implementation Notes

- 所有 AI 入口共享同一个 AIPreviewDialog 组件
- 只读展示 + 应用/取消按钮 + 覆盖警告（表单已有内容时显示）
- Apply 后向父页面 dispatch APPLY_AI_DRAFT 事件
- 父页面 reducer 处理写入逻辑
