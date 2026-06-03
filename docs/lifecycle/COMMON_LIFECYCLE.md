# Common Lifecycle Models

> 本文档定义所有页面共享的通用生命周期。每个页面从 `PAGE_LIFECYCLES.md` 引用这些通用模型，同时定义自己的专有生命周期。
>
> 核心公式：`state + event → newState → view`

---

## 1. Page Loading Lifecycle

页面从启动到就绪的基本生命周期。

```
NotMounted → Loading → Ready
                         ↓ Error → (RETRY) → Loading
Ready → Refreshing → Ready (或 Error)
```

### States

| State | 含义 |
|-------|------|
| NotMounted | 页面未初始化，无任何数据 |
| Loading | 正在从后端获取数据 |
| Ready | 数据加载完成，页面可交互 |
| Error | 加载失败，显示错误 |
| Refreshing | 手动刷新，保留上次数据 |

### Events

| Event | Payload | 触发方 |
|-------|---------|--------|
| INIT_PAGE | — | 页面 mount |
| LOAD_SUCCESS | records, stats | API 返回 |
| LOAD_FAILED | message | API 错误 |
| REFRESH | — | 用户点击刷新 |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| NotMounted | INIT_PAGE | Loading | 全页 loading spinner |
| Loading | LOAD_SUCCESS(data) | Ready | 内容填充 |
| Loading | LOAD_FAILED(msg) | Error | 错误提示 + 重试按钮 |
| Ready | REFRESH | Refreshing | 保留内容，显示刷新指示 |
| Refreshing | LOAD_SUCCESS(data) | Ready | 内容更新 |
| Refreshing | LOAD_FAILED(msg) | Ready | 保留上次数据，toast 错误 |
| Error | RETRY | Loading | 重新请求 |
| Error | INIT_PAGE | Loading | 同上 |

### Rules

- Error 状态**保留上次成功加载的数据**，不破坏现场
- Refreshing 期间**用户仍可浏览**上次数据
- 所有操作按钮在非 Ready 状态禁用（只读页面除外）
- INIT_PAGE 只触发一次（mount 时），后续刷新使用 REFRESH

---

## 2. Record Selection Lifecycle

左侧列表和右侧详情之间的选择关系。

```
EmptyList ← LOAD_EMPTY
NoSelection → RecordSelected
               ↓ delete
             SelectionLost → NoSelection (或 EmptyList)
```

### States

| State | 含义 |
|-------|------|
| EmptyList | 列表为空（无数据），显示空状态引导 |
| NoSelection | 列表有数据但未选中任何记录 |
| RecordSelected | 已选中记录，详情区显示 |
| SelectionChanging | 正在切换到另一条记录 |
| SelectionLost | 当前选中记录被外部删除，失去选中 |

### Events

| Event | 触发方 |
|-------|--------|
| SELECT_RECORD(id) | 用户点击列表项 |
| LOAD_EMPTY | 后端返回空列表 |
| FILTER_NO_RESULT | 搜索/筛选后无结果 |
| DELETE_SELECTED_RECORD | 删除当前选中记录 |
| SELECTION_RECOVERED | 自动回退到 records[0] |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| — | LOAD_SUCCESS([]) | EmptyList | 空状态插画 + "新建记录"按钮 |
| — | LOAD_SUCCESS(records) | RecordSelected(records[0]) | 列表填充，选中第一条 |
| EmptyList | FILTER_NO_RESULT | EmptyList | "没有匹配的记录" |
| RecordSelected | SELECT_RECORD(id) | RecordSelected | 右侧刷新为 id 的内容 |
| RecordSelected | DELETE_SELECTED_RECORD | SelectionLost | 显示删除确认 |
| SelectionLost | DELETE_SUCCESS + 仍有记录 | RecordSelected(records[0]) | 切换到第一条 |
| SelectionLost | DELETE_SUCCESS + 无记录 | EmptyList | 列表清空 |

### Rules

- EmptyList 和 NoSelection 状态右侧显示引导文字，不显示空表单
- 选中记录被删除后自动回退到 records[0]
- 搜索/筛选后如果当前选中记录不在结果中，进入 NoSelection

---

## 3. Draft Editing Lifecycle

表单编辑草稿的生命周期。**所有可编辑页面共享此模型**。

```
Clean → Editing → Dirty → Saving → Saved → Clean
                  ↑  ↓               ↓
                  │  CANCEL         SaveFailed → ConfirmDiscard → Cancelled
                  │    ↓                        ↑         ↓
                  └──── SWITCH_RECORD ──────────┘  保留并重试
                         (阻止或确认)
```

### States

| State | 含义 |
|-------|------|
| Clean | 草稿与已保存数据一致，无未保存变更 |
| Editing | 编辑弹窗已打开 |
| Dirty | 草稿与已保存数据不一致，存在未保存变更 |
| Saving | 正在向后端提交保存 |
| Saved | 保存成功，草稿与 server 同步 |
| SaveFailed | 保存失败，draft 保留，用户可以重试 |
| ConfirmDiscard | 保存失败后用户点击取消，询问是放弃还是保留 draft |
| Cancelled | 用户确认放弃编辑，不做任何写入 |

### Events

| Event | 触发方 |
|-------|--------|
| OPEN_EDITOR | 用户点击编辑按钮 / 新建 |
| UPDATE_DRAFT(partial) | 用户编辑任意字段 |
| SAVE_REQUEST | 用户点击保存 |
| SAVE_SUCCESS(record) | API 返回成功 |
| SAVE_FAILED(msg) | API 返回错误 |
| CANCEL_EDIT | 用户关闭弹窗 / 取消 |
| SWITCH_RECORD | 用户选择另一条记录 |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| Clean | OPEN_EDITOR | Editing | 弹窗打开，预填数据 |
| Editing | UPDATE_DRAFT | Dirty | 表单实时更新 |
| Dirty | UPDATE_DRAFT | Dirty | 继续编辑 |
| Dirty | SAVE_REQUEST | Saving | 保存按钮禁用 |
| Dirty | CANCEL_EDIT | Cancelled | 弹窗关闭，不保存 |
| Dirty | SWITCH_RECORD | Dirty | 阻止切换，提示"先保存或放弃" |
| Saving | SAVE_SUCCESS(record) | Saved | 弹窗关闭，列表更新 |
| Saving | SAVE_FAILED(msg) | SaveFailed | 错误提示 |
| SaveFailed | SAVE_REQUEST | Saving | 重试保存 |
| SaveFailed | CANCEL_EDIT | ConfirmDiscard | 询问"放弃修改？保留并重试？" |
| ConfirmDiscard | CONFIRM_DISCARD | Cancelled | 放弃编辑，关闭弹窗 |
| ConfirmDiscard | CANCEL_DISCARD | SaveFailed | 保留 draft，继续编辑 |
| Saved | — | Clean | 编辑完成 |

### Rules

- **Dirty 不能静默丢失**。关闭弹窗、切换记录、关闭页面时必须提示用户
- SaveFailed 后**保留 draft**，用户可以选择重试保存或确认放弃
- SaveFailed 后点击取消**不直接关闭**，必须先进入 ConfirmDiscard 让用户选择"放弃修改"或"保留并重试"
- Saved 后通过 SAVE_SUCCESS 的返回值同步到正式记录
- Saving 期间**不允许重复提交**（保存按钮禁用）
- 新建和编辑复用同一条生命周期（初始状态都是 Clean）

---

## 4. Auto Save Lifecycle

适用于日记、自我分析、作品感悟等长文本页面的自动保存机制。

```
Idle → DirtyWaiting → (debounce 3s) → AutoSaving → AutoSaved → Idle
                                          ↓
                                    AutoSaveFailed → DirtyWaiting（重试）
```

### States

| State | 含义 |
|-------|------|
| Idle | 无未保存变更，或已保存 |
| DirtyWaiting | 有未保存变更，正在等待 debounce 计时器 |
| AutoSaving | 正在自动保存 |
| AutoSaved | 自动保存成功 |
| AutoSaveFailed | 自动保存失败 |

### Events

| Event | 触发方 |
|-------|--------|
| DRAFT_CHANGED | 用户输入（每次按键） |
| DEBOUNCE_TIMEOUT | 用户停止输入超过 3 秒 |
| AUTO_SAVE_SUCCESS | 后端保存成功 |
| AUTO_SAVE_FAILED | 后端保存失败 |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| Idle | DRAFT_CHANGED | DirtyWaiting | 显示"未保存"标记 |
| DirtyWaiting | DRAFT_CHANGED | DirtyWaiting | 重置 debounce 计时器 |
| DirtyWaiting | DEBOUNCE_TIMEOUT | AutoSaving | 触发保存 |
| AutoSaving | AUTO_SAVE_SUCCESS | AutoSaved | "已自动保存"toast |
| AutoSaving | AUTO_SAVE_FAILED | AutoSaveFailed | 显示弱提示："自动保存失败，内容仍保留，可继续编辑或手动保存" |
| AutoSaveFailed | DRAFT_CHANGED | DirtyWaiting | 下次输入后重新等待 |
| AutoSaved | DRAFT_CHANGED | DirtyWaiting | 新编辑触发新周期 |

### Rules

- **自动保存失败不能清空正文**或丢弃 draft，必须保留 draft
- 自动保存失败**不显示全页错误**
- 但必须在状态栏或 toast 显示弱提示："自动保存失败，内容仍保留，可继续编辑或手动保存"
- 手动保存和自动保存共享保存接口，但不能同时触发
- debounce 时间 3 秒（基于 AutoSaveMixin 历史实现）
- 自动保存的 draft 数据与手动保存的 draft 是同一份
- 切换记录前如果 DirtyWaiting，先触发一次保存再切换
- 自动保存失败后，下次输入或手动保存可以重试

---

## 5. Delete Lifecycle

软删除的生命周期。**所有模块统一使用此模型**。

```
Idle → ConfirmingDelete → Deleting → Deleted (soft)
                              ↓
                        DeleteFailed → Idle
```

### States

| State | 含义 |
|-------|------|
| Idle | 无删除操作 |
| ConfirmingDelete | 确认弹窗已显示 |
| Deleting | 正在向后端发送删除请求 |
| Deleted | 删除成功（软删除，数据仍存在但不显示） |
| DeleteFailed | 删除失败 |

### Events

| Event | 触发方 |
|-------|--------|
| DELETE_REQUEST(id) | 用户点击删除按钮 |
| DELETE_CONFIRM | 用户在确认弹窗点击"确定" |
| DELETE_CANCEL | 用户点击"取消"或关闭弹窗 |
| DELETE_SUCCESS(id) | API 返回成功 |
| DELETE_FAILED(msg) | API 返回错误 |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| Idle | DELETE_REQUEST(id) | ConfirmingDelete | 显示确认弹窗 |
| ConfirmingDelete | DELETE_CONFIRM | Deleting | 弹窗关闭，执行删除 |
| ConfirmingDelete | DELETE_CANCEL | Idle | 弹窗关闭，无变化 |
| Deleting | DELETE_SUCCESS(id) | Deleted | 列表移除，右侧回退 |
| Deleting | DELETE_FAILED(msg) | Idle | 错误提示，保留原数据 |

### Rules

- **删除必须确认**，不存在"直接删除"
- 删除失败**不能移除 UI 中的记录**
- 软删除：`deleted=true` + `deleted_at`，数据不物理删除
- 当前选中记录被删除后，自动回退到剩余记录的第一条
- 无剩余记录时进入 EmptyList

---

## 6. Attachment / Image Lifecycle

适用于日记、足迹、作品感悟、自我分析、教训与反思等含图片的模块。

```
Collapsed → Expanded → Picking → Uploading → Uploaded
                      ↑            ↓
                      │        UploadFailed → (重试)
                      │
                   Removing / Reordered
```

### States

| State | 含义 |
|-------|------|
| Collapsed | 图片区折叠（默认收起） |
| Expanded | 图片区展开，显示缩略图列表 |
| Picking | 系统文件选择器打开（用户选图） |
| Uploading | 图片上传中（base64 → 后端） |
| Uploaded | 图片上传完成 |
| Removing | 正在删除图片 |
| Failed | 上传或删除失败 |

### Events

| Event | 触发方 |
|-------|--------|
| EXPAND_ATTACHMENTS | 用户展开/收起 |
| PICK_IMAGES | 用户点击添加图片 |
| UPLOAD_SUCCESS(image) | 上传成功 |
| UPLOAD_FAILED(msg) | 上传失败 |
| REMOVE_IMAGE(name) | 用户点击删除 |
| REORDER_IMAGES(names[]) | 用户拖拽排序 |

### Rules

- 图片区默认折叠，不抢占正文空间
- 上传失败不丢失已上传图片
- 删除图片需要确认（或允许撤销）
- 图片排序通过 `REORDER_IMAGES` 事件更新 `images[]` 数组顺序

---

## 7. AI Preview Lifecycle

所有 AI 功能的共用预览确认状态机。**任何 AI 入口都必须经过此生命周期**。

```
Idle → Requesting → Previewing → Applying → Applied
                      ↓             ↓
                    Failed ← →  Cancelled
```

### States

| State | 含义 |
|-------|------|
| Idle | 无 AI 操作 |
| Requesting | AI API 请求中 |
| Previewing | AI 结果已返回，以只读形式展示给用户 |
| Applying | 用户确认，正在将 AI 内容写入 draft |
| Applied | 写入完成 |
| Cancelled | 用户取消，不改变任何数据 |
| Failed | AI 调用失败或返回非法 JSON |

### Events

| Event | 触发方 |
|-------|--------|
| OPEN_AI | 用户点击任一 AI 按钮 |
| RECEIVE_AI_DRAFT(draft) | AI API 返回合法结果 |
| APPLY_AI_DRAFT | 用户点击预览弹窗的"应用" |
| CANCEL_AI_DRAFT | 用户点击"取消"或关闭弹窗 |
| AI_FAILED(message, raw?) | API 超时、网络错误、非法 JSON |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| Idle | OPEN_AI | Requesting | 加载指示器 |
| Requesting | RECEIVE_AI_DRAFT(draft) | Previewing | 显示 AI 预览弹窗（只读） |
| Requesting | AI_FAILED(msg, raw) | Failed | 显示错误 + 原始返回 |
| Previewing | APPLY_AI_DRAFT | Applying | 关闭弹窗，写入中 |
| Previewing | CANCEL_AI_DRAFT | Cancelled | 关闭弹窗，无变化 |
| Applying | 写入完成 | Applied | 视图更新 |
| Failed | RETRY | Requesting | 重新请求 |
| Failed | CANCEL_AI_DRAFT | Cancelled | 关闭错误提示 |

### Rules

- **AI 结果不能直接写入正式数据**，必须先进入 Previewing
- Previewing 只读展示，用户必须主动选择 APPLY 或 CANCEL
- APPLY 将 AI 内容写入父页面的 draft（不直接写入 server）
- CANCEL **不改变任何数据**
- 非法 JSON 进入 Failed 状态并显示原始返回
- Requesting 状态不能重复发起 AI 请求

---

## 8. Export Lifecycle

适用于日记导出、模块导出、全部数据导出等场景。

```
Idle → Exporting → Exported → Idle
          ↓
     ExportFailed
```

### States

| State | 含义 |
|-------|------|
| Idle | 无导出操作 |
| Exporting | 正在执行导出 |
| Exported | 导出完成 |
| ExportFailed | 导出失败 |

### Events

| Event | 触发方 |
|-------|--------|
| EXPORT_REQUEST(format, params) | 用户点击导出按钮 |
| EXPORT_SUCCESS(path) | 导出完成，返回文件路径 |
| EXPORT_FAILED(message) | 导出失败 |

### Transitions

| Current | Event | Next | View |
|---------|-------|------|------|
| Idle | EXPORT_REQUEST(format) | Exporting | 导出按钮禁用，显示加载 |
| Exporting | EXPORT_SUCCESS(path) | Exported | 显示"导出成功" + 文件路径 |
| Exporting | EXPORT_FAILED(msg) | ExportFailed | 显示错误 |
| ExportFailed | EXPORT_REQUEST | Exporting | 重试 |
| Exported | — | Idle | 恢复空闲 |

### Rules

- 导出**不改变正式数据**
- 导出失败**不影响原记录**
- 导出成功必须显示导出路径
- 导出期间不阻止用户浏览，但相关导出按钮禁用
