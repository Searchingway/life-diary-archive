# HANDOFF — Desktop 3.3 AI 辅助计划版

## 修改了哪些文件

共 **6 个新增文件** + **11 个修改文件**：

### 新增文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/ai_service.py` | AI 服务层：DeepSeek API 调用、配置读写、超时错误处理、JSON 模式、API Key 掩码日志 |
| `src/life_dairy/ai_dialogs.py` | AI 对话组件：AISettingsDialog（配置弹窗）、AIPreviewDialog（预览确认弹窗） |
| `src/life_dairy/action_plan_storage.py` | 行动计划存储层：ActionPlanItem + ActionPlanTask 数据类 + ActionPlanStorage CRUD |
| `src/life_dairy/action_plan_page.py` | 行动计划页面：ActionPlanPage（AutoSaveMixin, QWidget），完整 CRUD + 子任务管理 |
| `tests/test_ai_service.py` | AI 配置测试 7 项 |
| `tests/test_action_plan_storage.py` | 行动计划存储测试 9 项 |

### 修改文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/__init__.py` | `3.2.0` → `3.3.0` |
| `src/life_dairy/app.py` | 导入 ActionPlanStorage，传入 DiaryMainWindow |
| `src/life_dairy/main_window.py` | 导入 ActionPlanPage + ActionPlanStorage，新增「行动计划」页签（索引 4），连接 plan_page.action_plan_created 信号 |
| `src/life_dairy/plan_page.py` | 新增「AI 补全计划」按钮、AI 补全方法、AI 拆解为行动计划功能 + _DecomposeDialog |
| `src/life_dairy/thought_page.py` | 新增「AI 整理思考」按钮和方法 |
| `src/life_dairy/resource_page.py` | 新增「AI 评估资源」按钮和方法 |
| `src/life_dairy/data_manager_page.py` | 新增「AI 设置」按钮和 open_ai_settings 方法 |
| `src/life_dairy/overview.py` | OverviewService 接入 action_plan_storage，新增 _action_plan_items() 时间线，模块统计新增「行动计划」 |
| `src/life_dairy/overview_page.py` | 新增「今日行动任务」区域，基础统计新增行动计划总数/进行中/今日待办 |
| `src/life_dairy/backup_service.py` | KNOWN_MODULES/MODULE_METADATA/MODULE_LABELS 新增 action_plans、info_memos、notes |
| `tests/test_main_window.py` | 页签数量从 13 更新为 14，页签列表新增 action_plan_page |

## AI 配置保存在哪里

`data/Diary/config/ai_settings.json`

配置字段：
- `api_key`: DeepSeek API Key
- `base_url`: API 地址（默认 https://api.deepseek.com）
- `model`: 模型名（默认 deepseek-chat）
- `enabled`: 是否启用 AI 功能
- `timeout_seconds`: 超时秒数（默认 60）

`data/` 目录已在 `.gitignore` 中排除，API Key 不会提交到 Git。

## DeepSeek 如何调用

1. 用户通过数据管理页 → AI 设置填写 API Key 等信息
2. 启用 AI 后，各页面点击 AI 按钮
3. `ai_service.py` 读取配置，使用 openai 库调用 DeepSeek API（OpenAI 兼容接口）
4. 支持 JSON 模式（response_format: json_object）和普通文本模式
5. 调用失败时返回中文错误提示；超时、未配置、API 错误分别提示

## 轻计划/轻思考/轻资源分别增加了什么 AI 入口

| 模块 | 按钮 | 功能 |
|------|------|------|
| 轻计划 | AI 补全计划 | 根据表单内容生成标题、类型、优先级、状态、建议步骤、风险点、下一步行动 |
| 轻计划 | AI 拆解为行动计划 | 选择日期范围，AI 生成按日排列的任务列表，确认后自动创建行动计划 |
| 轻思考 | AI 整理思考 | 根据标题/描述/已有想法生成问题重述、选项、风险、支持/反对理由、结论、下一步行动 |
| 轻资源 | AI 评估资源 | 根据标题/描述/资源项生成时间/金钱/精力/情绪成本分析、总体判断、轮回测试建议 |

所有 AI 结果必须在预览弹窗中确认后才应用，不允许直接保存或覆盖。

## 行动计划如何存储

- 目录：`data/Diary/action_plans/{uuid}/action_plan.json`
- 单 JSON 文件存储（Pattern B）
- 字段：id, title, plan_type, description, start_date, end_date, daily_available_time, priority, status, source_light_plan_id, tasks[], summary
- 子任务字段：id, title, date, estimated_minutes, done, note
- 软删除机制与现有模块一致

## AI 拆解如何生成行动计划

1. 用户在轻计划页面选择一个已有计划，点击「AI 拆解为行动计划」
2. 弹窗输入开始日期、截止日期、每日可用时间
3. 调用 DeepSeek（JSON 模式），要求返回按日排列的任务列表
4. 如果 AI 返回不是合法 JSON，提示用户并显示原始返回，不崩溃
5. 预览弹窗显示任务列表，用户确认后自动创建行动计划
6. 行动计划保留 source_light_plan_id 字段记录来源

## 是否保护 API Key

是：
- API Key 输入框使用密码模式（EchoMode.Password）
- `_mask_key()` 函数在日志中只显示前 4 位 + **** + 后 4 位
- 不在日志中打印用户输入全文和 API Key
- `data/` 目录已在 .gitignore 中排除

## 实际运行了哪些测试

```
python -m pytest tests/ -v --tb=short
```

共 116 个测试：
- 112 passed
- 4 failed（均为已有失败，非本轮引入）
- 新增 16 个测试全部通过

新增测试详情：
- `test_ai_service.py`（7 项）：配置加载/保存/默认值、未启用/无 Key 错误、Key 掩码
- `test_action_plan_storage.py`（9 项）：CRUD、状态/类型筛选、搜索、进度计算、今日任务、重启持久化

## 测试结果

| 类别 | 数量 | 状态 |
|------|------|------|
| 新增测试 | 16 | 全部通过 |
| 已有测试 | 100 | 96 通过，4 已有失败 |
| 总计 | 116 | 112 通过 |

已有失败（非本轮引入）：
- `test_work_changes_can_auto_save_and_manual_save_still_works` — KeyError: 'one_sentence'
- `test_list_entries_in_date_range_returns_oldest_first` — 排序断言不一致
- `test_list_works_can_search_title_tags_body_status_and_filter_type` — 编码问题
- `test_save_and_reload_work_with_relations` — 编码问题

## 当前风险

| 风险 | 等级 | 说明 |
|------|------|------|
| AI 依赖 openai 库 | 中 | 用户需要 `pip install openai` 才能使用 AI 功能，非 AI 功能不受影响 |
| AI 调用网络依赖 | 中 | 需要网络连接和有效的 DeepSeek API Key，调用失败不影响原有功能 |
| 总览页新增 UI 区域 | 低 | 新增「今日行动任务」区域，不影响原有统计和时间线 |
| 页签索引变更 | 低 | 新增行动计划页签导致索引从 4 开始全部 +1，已同步更新所有集成点 |
| 已有测试失败 | 低 | 4 个已有失败非本轮引入，不影响新功能 |

## 是否建议 git commit

**建议提交。** 本轮新增的 AI 功能遵循「预览-确认-应用」的安全模式，不自动覆盖用户数据。行动计划模块遵循现有存储模式，不影响手机版和其他模块。

建议 commit message：

```
Desktop 3.3：AI 辅助计划版

- 新增 ai_service.py：DeepSeek API 调用、配置管理、超时/错误处理
- 新增 ai_dialogs.py：AI 设置弹窗、预览确认弹窗
- 新增 action_plan_storage.py + action_plan_page.py：行动计划完整 CRUD
- 轻计划新增「AI 补全计划」和「AI 拆解为行动计划」按钮
- 轻思考新增「AI 整理思考」按钮
- 轻资源新增「AI 评估资源」按钮
- 数据管理页新增 AI 设置入口
- 总览页新增行动计划统计和今日行动任务
- 版本号 3.2.0 → 3.3.0
- 新增 16 个测试，全部通过
```
