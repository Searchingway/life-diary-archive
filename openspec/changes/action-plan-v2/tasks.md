# 实现任务 — ActionPlan V2

> 所有任务未完成。

## 1. 数据层确认

- [ ] 1.1 确认 `action_plan_storage.py` 的 `ActionPlanTask` 已兼容 startDate/endDate/progress/scheduledDate/dependsOn/chainX/chainY 字段
- [ ] 1.2 旧数据只有 `date` 字段时，兼容转换为 `scheduledDate=date`、`startDate=date`、`endDate=date`
- [ ] 1.3 确认 `data_api.py` 的 `save_generic_record()` 正确处理 tasks 数组中的新字段
- [ ] 1.4 确认 `list_module_records()` 返回完整的 `extra.tasks`（含新字段）

## 2. ActionPlanPage 外壳

- [ ] 2.1 实现左侧 sidebar：搜索框 + 状态筛选 + 计划列表显示（标题/类型/状态/进度%）
- [ ] 2.2 实现右侧头部：当前计划标题/类型/状态/优先级/进度条 + [编辑计划] [AI 拆解] 按钮
- [ ] 2.3 实现视图切换 Tab：时间表 | 甘特图 | 任务链
- [ ] 2.4 实现底部工具栏：[添加任务] [编辑所选] [删除所选]
- [ ] 2.5 实现空状态（无计划时引导）
- [ ] 2.6 实现删除计划确认弹窗

## 3. Today View（时间表）

- [ ] 3.1 任务按 `scheduledDate` 分组。无 scheduledDate 的任务归入"未安排"组。
- [ ] 3.2 每个任务显示：勾选框 + 标题 + 预计耗时 + 备注
- [ ] 3.3 勾选后任务样式变化（删除线 / 颜色淡化）
- [ ] 3.4 进度条随勾选更新
- [ ] 3.5 "今天"日期组标注 "今天"
- [ ] 3.6 逾期任务（scheduledDate < today && !done）标注 "逾期 N 天"
- [ ] 3.7 空任务显示 "还没有任务"

## 4. Gantt View（甘特图）

- [ ] 4.1 时间横轴：从计划 startDate 到 endDate，每天一列
- [ ] 4.2 每个任务一行，左侧显示任务标题
- [ ] 4.3 任务条左边界位置由 `startDate` 决定
- [ ] 4.4 任务条宽度由 `endDate - startDate + 1 天` 决定，**不使用 `estimatedMinutes`**
- [ ] 4.5 任务条内部按 `progress` 显示进度填充色
- [ ] 4.6 已完成任务颜色变灰
- [ ] 4.7 支持拖动任务条整体移动日期范围（同时偏移 startDate 和 endDate，跨度不变）
- [ ] 4.8 支持拖动任务条左边缘修改 `startDate`
- [ ] 4.9 支持拖动任务条右边缘修改 `endDate`
- [ ] 4.10 拖拽后 debounce 500ms 自动保存
- [ ] 4.11 校验 `startDate <= endDate`，违反时阻止操作
- [ ] 4.12 `estimatedMinutes` 只显示在 tooltip 中
- [ ] 4.13 任务超出视图时支持水平滚动
- [ ] 4.14 空任务显示 "还没有任务"

## 5. Chain View（任务链）

- [ ] 5.1 深色背景画布（React 中用 SVG/Canvas 实现）
- [ ] 5.2 优先使用 `dependsOn` 生成任务间连接线
- [ ] 5.3 无 `dependsOn` 时按 `startDate / scheduledDate / 创建顺序` 自动布局
- [ ] 5.4 每个任务一个圆形节点
- [ ] 5.5 节点位置优先使用 `chainX / chainY`，无坐标时自动布局
- [ ] 5.6 已完成节点亮绿色，未完成蓝色渐变
- [ ] 5.7 悬停显示 tooltip（标题/日期/耗时/状态/备注）
- [ ] 5.8 支持拖拽节点
- [ ] 5.9 拖拽只改变 `chainX / chainY`，不改变 `startDate / endDate / dependsOn`
- [ ] 5.10 拖拽后 debounce 500ms 保存坐标
- [ ] 5.11 双击节点打开任务编辑弹窗
- [ ] 5.12 删除任务时清理其他任务的 `dependsOn` 引用
- [ ] 5.13 检测循环依赖（设置 dependsOn 时），存在循环时阻止
- [ ] 5.14 空任务显示 "还没有任务"

## 6. 弹窗组件

- [ ] 6.1 PlanEditDialog：标题 / 类型 / 描述 / 开始日期 / 截止日期 / 每日可用时间 / 优先级 / 状态 / 完成总结
- [ ] 6.2 TaskEditDialog：标题 / scheduledDate / startDate / endDate / 预计耗时 / 备注 / 已完成 / 前置任务
- [ ] 6.3 新建计划弹窗 = 编辑弹窗（空字段）
- [ ] 6.4 弹窗保存后刷新列表和视图

## 7. AI 拆解流程

- [ ] 7.1 AIBreakdownDialog：开始日期 / 截止日期 / 每日可用时间
- [ ] 7.2 提交后调用 AI API（通过后端代理）
- [ ] 7.3 AI 返回的任务必须包含 `startDate / endDate / progress / scheduledDate / dependsOn`
- [ ] 7.4 如果 AI 只返回 `date`（旧格式），兼容转换为 `scheduledDate = date`、`startDate = date`、`endDate = date`
- [ ] 7.5 RECEIVE_AI_DRAFT → 显示 AIPreviewDialog
- [ ] 7.6 APPLY_AI_DRAFT → 替换当前计划的 title/planType/tasks
- [ ] 7.7 CANCEL_AI_DRAFT → 无变化
- [ ] 7.8 AI_RESPONSE_INVALID → 显示错误 + 原始返回
- [ ] 7.9 AI_FAILED → 显示错误

## 8. 集成测试

- [ ] 8.1 手动测试：新建计划 → 添加任务（含日期范围） → 勾选完成 → 进度更新
- [ ] 8.2 手动测试：切换 today / gantt / chain 视图
- [ ] 8.3 手动测试：甘特图整体拖动任务条到新日期范围
- [ ] 8.4 手动测试：甘特图拖动左边缘调整 startDate
- [ ] 8.5 手动测试：甘特图拖动右边缘调整 endDate
- [ ] 8.6 手动测试：甘特图 startDate > endDate 时被阻止
- [ ] 8.7 手动测试：任务链拖拽节点 → 刷新后 chainX/chainY 保留
- [ ] 8.8 手动测试：设置任务依赖 → 链视图正确显示连线
- [ ] 8.9 手动测试：形成循环依赖时被阻止
- [ ] 8.10 手动测试：删除被依赖的任务 → 依赖引用被清理
- [ ] 8.11 手动测试：AI 拆解 → 预览 → 应用
- [ ] 8.12 手动测试：AI 返回非法 JSON → 显示原始返回
- [ ] 8.13 手动测试：旧数据只有 date 字段 → 兼容显示
- [ ] 8.14 手动测试：删除计划后列表和视图正确回退
- [ ] 8.15 手动测试：空计划（0 任务）各视图正常
- [ ] 8.16 手动测试：所有任务完成后进度 100%
- [ ] 8.17 手动测试：重启应用后数据持久化
