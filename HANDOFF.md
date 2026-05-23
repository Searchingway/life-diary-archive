# HANDOFF — Desktop 3.2 信息备忘模块

## 修改了哪些文件

共 **2 个新增文件** + **5 个修改文件**：

### 新增文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/info_memo_storage.py` | 信息备忘存储层：`InfoMemoEntry` 数据类 + `InfoMemoStorage` 存储类，遵循 `thought_storage.py` 的单 JSON 模式 |
| `src/life_dairy/info_memo_page.py` | 信息备忘页面：`InfoMemoPage`（AutoSaveMixin, QWidget），sidebar + editor 布局，QStackedWidget 切换三种类型专属字段 |
| `docs/test/05_测试清单.md` | 新增测试清单，覆盖 CRUD、搜索、筛选、导航、自动保存、兼容性 |

### 修改文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/__init__.py` | `3.1.0` → `3.2.0` |
| `src/life_dairy/app.py` | 导入 `InfoMemoStorage`，传入 `DiaryMainWindow` |
| `src/life_dairy/main_window.py` | 导入 `InfoMemoPage` + `InfoMemoStorage`，新增 info_memo_page 页签（索引 6），更新 tab 标题映射、_editable_pages、_reload_data_after_restore、_open_timeline_record、_create_overview_service |
| `src/life_dairy/overview.py` | 导入 `InfoMemoStorage`，`OverviewService` 接入 info_memo_storage，`build_timeline()` 新增 `_info_memo_items()`，`build_module_summary()` 新增「信息备忘」模块 |
| `README.md` | 版本号 3.2，新增信息备忘模块说明，数据目录，页签列表，当前范围，版本历史 |
| `TODO` | 新增信息备忘条目 |
| `docs/dev-notes/tech_debt_plan.md` | 新增 Desktop 3.2 已完成项和后续遗留问题 |

## 每个文件改了什么

### 1. 信息备忘存储层（新增）

**`src/life_dairy/info_memo_storage.py`** — 遵循 `thought_storage.py` 的模式：
- `InfoMemoEntry` 数据类：通用字段（id, title, info_type, status, priority, tags, source, link, local_path, note, created_at, updated_at）+ `type_fields` 字典存储类型专属字段
- `InfoMemoStorage` 存储类：`list_info_memos`/`load_memo`/`save_memo`/`delete_memo`
- 搜索覆盖：title, tags, source, link, note, type_fields 全部值（含 customer, intermediary, executor, course_name, platform, direction 等）
- 数据目录：`data/Diary/info_memos/{uuid}/info_memo.json`

### 2. 信息备忘页面（新增）

**`src/life_dairy/info_memo_page.py`** — 遵循 `thought_page.py` 的模式：
- `InfoMemoPage(AutoSaveMixin, QWidget)` sidebar + editor 布局
- **Sidebar**：搜索框、类型筛选、状态筛选（联动）、新建按钮、删除按钮、列表
- **Editor**：保存/恢复按钮、基本信息分组（标题、类型、状态、优先级、标签、来源、链接、路径、备注）
- **QStackedWidget 三页**：
  - 页 0 - 接单记录：客户/需求方、中介/介绍人、实际执行人、接单日期、截止日期、工期天数、报价、定金、尾款、交付内容
  - 页 1 - 网课资源：课程名称、平台/网站、课程链接、学习方向、购买状态、当前进度、想学原因
  - 页 2 - 通用信息：分类、主要内容、提醒日期
- 类型切换时：保存当前页 type_fields → 切换 QStackedWidget 页 → 更新状态下拉 → 加载新页 type_fields
- 自动保存：_auto_save_now 只调用 _read_form() 和 save_memo()，不调用 _fill_form()，不跳光标

### 3. 主窗口集成

- 页签索引 6：「信息备忘」插入在「轻资源」（5）后、「自我观察」（7）前
- 窗口标题：`Desktop 3.2 - 信息备忘`
- `_update_tab_titles` 改为 12 个页签的索引映射
- `_editable_pages` 新增 `self.info_memo_page`
- `_reload_data_after_restore` 完整重置 info_memo 存储和页面
- `_open_timeline_record` 新增 `info_memos` 路由分支

### 4. 总览集成

- `OverviewService.__init__` 新增 `info_memo_storage` 参数
- `build_timeline()` 调用 `_info_memo_items()` 生成 TimelineItem（显示记录类型、标题、摘要、状态、来源模块）
- `build_module_summary()` 新增「信息备忘」模块统计

## 数据存储

- **目录**：`data/Diary/info_memos/{uuid}/info_memo.json`
- **存储模式**：单 JSON 文件（Pattern B），与 thoughts、resources、observations 一致
- **软删除**：与现有模块一致，设置 `deleted: true` + `deleted_at`
- **备份恢复**：info_memos/ 目录自然包含在 data/Diary/ 的 zip 备份中，无需额外配置

## 信息备忘支持哪些类型

| 类型 | 专属字段 | 可用状态 |
|------|----------|----------|
| 接单记录 | customer, intermediary, executor, order_date, deadline, duration_days, price, deposit, final_payment, deliverables | 沟通中、已接单、进行中、待验收、已交付、已结款、已取消 |
| 网课资源 | course_name, platform, course_url, direction, paid_status, progress, reason | 想看、已收藏、学习中、暂停、已学完、放弃 |
| 通用信息 | category, content, reminder_date | 未处理、已记录、处理中、已完成、已归档 |

## 搜索和筛选如何实现

- **搜索**：`InfoMemoStorage._matches_query()` 搜索 title、tags、source、link、note 和 type_fields 所有值（flatten 为字符串）
- **类型筛选**：sidebar type_filter_combo，选中后刷新列表，同时联动更新 status_filter_combo 的选项
- **状态筛选**：sidebar status_filter_combo，选中后刷新列表
- **类型+状态联动**：`_on_type_filter_changed()` 根据选中类型更新状态下拉选项，若当前选中状态不在新选项中则重置为「全部」

## 总览页是否接入

是。总览页时间线中显示「信息备忘」记录（日期、类型、标题、状态、摘要），双击可跳转到对应记录。模块统计区域显示信息备忘记录数量和最近更新时间。

## 实际运行了哪些测试

目前为人工验证清单（docs/test/05_测试清单.md）。待补充自动化测试。

## 当前风险

| 风险 | 等级 | 说明 |
|------|------|------|
| 新模块无自动化测试 | 中 | 当前仅有手工测试清单，尚未编写 unittest |
| type_fields 数据验证宽松 | 低 | type_fields 以 dict 存储，类型不匹配时会用默认值填充，不抛异常 |
| 双 SpinBox 精度 | 低 | QDoubleSpinBox 默认 2 位小数，保存到 JSON 可能丢失精度；JSON 读取时使用 float() 转换 |
| 未实现类型转换按钮 | 低 | 信息备忘一期仅 CRUD，未实现转轻计划/教训反思等功能 |
| 提醒日期无提醒功能 | 低 | reminder_date 仅为文本字段，不做推送/弹窗提醒 |

## 是否建议 Git commit

**建议提交。** 本轮修改是完全独立的新模块，不涉及旧模块重构或数据迁移，不影响现有功能。

建议 commit message：

```
3.2 桌面版：新增信息备忘模块

- 新增 src/life_dairy/info_memo_storage.py：InfoMemoEntry + InfoMemoStorage
- 新增 src/life_dairy/info_memo_page.py：InfoMemoPage，支持三种类型 CRUD
- 顶部导航新增「信息备忘」页签（轻资源后、自我观察前）
- 总览页时间线和模块统计接入信息备忘
- 搜索覆盖标题/标签/来源/链接/备注/客户/中介/课程平台等字段
- 类型筛选和状态筛选联动
- 接入自动保存，不跳光标
- 版本号 3.1.0 → 3.2.0
- 新增 docs/test/05_测试清单.md
- 更新 README、HANDOFF、TODO、tech_debt_plan
```

---

## Round 1 工程整理（重构前准备）

### 修改了哪些文件

| 文件 | 说明 |
|------|------|
| `电脑直装版/specs/人生档案.spec` | 标记为 DEPRECATED，hiddenimports/binaries 不完整 |
| `src/life_dairy/main_window.py` | 窗口标题改为读取 `__version__`，消除硬编码 |
| `android/.../AndroidManifest.xml` | `allowBackup="true"` → `"false"`，本地优先隐私设计 |
| `pyproject.toml` | 版本号 3.1.0 → 3.2.0，与 `__init__.py` 一致 |
| `docs/release/BUILD_RELEASE.md` | 版本号 3.0.1 → 3.2.0，写明唯一推荐打包入口 |
| `docs/test/TEST_CHECKLIST.md` | 版本号 3.0.1 → 3.2.0 |
| `README.md` | 描述从 "Desktop 3.1 工程结构整理版" 更新为 "Desktop 3.2" |
| `docs/dev-notes/tech_debt_plan.md` | 补充 Round 1 完成事项 |

### 验收结果

- [x] 唯一正式打包入口：`packaging/windows/LifeDiary.spec`
- [x] 窗口标题：`人生档案 Diary Desktop 3.2.0 - 信息备忘`
- [x] `allowBackup="false"`
- [x] 全部 14 个测试文件通过（运行 `python -m pytest tests/ -v --tb=short`）
- [x] 源码能正常启动

### 当前风险

| 风险 | 等级 | 说明 |
|------|------|------|
| 旧 spec 仍存在于项目中 | 低 | 已标记 DEPRECATED，不可删除以免破坏已有构建脚本 |
| 版本号一致 | 低 | `__init__.py`、`pyproject.toml`、文档已同步为 3.2.0 |

### Round 2 计划

- 抽取 `image_utils.py`：将 7 个 Storage 中的 `_sync_images` / `_copy_image` / `_unique_name` / `_prune_unused_images` 合并到公共工具类

---

## 笔记功能（新增）

### 新增文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/note_storage.py` | 笔记存储层：`NoteEntry` 数据类 + `NoteStorage` CRUD，单 JSON 文件存储 |
| `src/life_dairy/note_page.py` | 笔记页面：`NotePage(AutoSaveMixin, QWidget)`，sidebar + editor 布局 |
| `tests/test_note_storage.py` | 存储层测试 11 项：to_dict/from_dict、CRUD、搜索、软删除 |
| `tests/test_note_page.py` | UI 测试 15 项：初始化、表单填充/读取、脏状态、保存/删除、自动保存、搜索 |

### 修改文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/main_window.py` | 导入 NotePage + NoteStorage，新增 note_page 页签（索引 6），更新所有集成点 |
| `src/life_dairy/overview.py` | 导入 NoteStorage，新增 notes 模块统计和时间线项 |
| `src/life_dairy/app.py` | 导入 NoteStorage，传入 DiaryMainWindow |
| `TODO` | 新增笔记条目 |
| `docs/test/05_测试清单.md` | 新增笔记功能测试项 |

### 数据存储
- **目录**：`data/Diary/notes/{uuid}/note.json`
- **字段**：id, title, description, body, created_at, updated_at
- **软删除**：与现有模块一致
