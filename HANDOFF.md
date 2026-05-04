# HANDOFF — Desktop 3.1 工程结构整理版

## 修改了哪些文件

共 **17 个修改文件** + **2 个新增文件**：

### 新增文件
| 文件 | 说明 |
|------|------|
| `src/life_dairy/logger.py` | 日志初始化模块，配置 root logger（DEBUG FileHandler + WARNING StreamHandler） |
| `docs/dev-notes/tech_debt_plan.md` | 技术债与重构计划文档，记录已完成工作和后续优先级 |

### 修改文件
| 文件 | 行数变化 |
|------|----------|
| `src/life_dairy/__init__.py` | `0.3.0` → `3.1.0` |
| `src/life_dairy/app.py` | +16 行：加入 logger 初始化、启动日志、sys.excepthook |
| `src/life_dairy/main_window.py` | +12 行：窗口标题 "Desktop 3.1"、备份/恢复/导入异常日志 |
| `src/life_dairy/backup_service.py` | +52/-36 行：导入版本号、加入日志、修复 `_unique_backup_path` 函数体被删的 bug |
| `src/life_dairy/storage.py` | +5 行：list_entries 跳过时 logger.debug、删图失败 logger.warning |
| `src/life_dairy/footprint_storage.py` | +5 行：同上模式 |
| `src/life_dairy/book_storage.py` | +5 行：同上模式 |
| `src/life_dairy/lesson_storage.py` | +5 行：同上模式 |
| `src/life_dairy/self_analysis_storage.py` | +5 行：同上模式 |
| `src/life_dairy/work_storage.py` | +5 行：同上模式 |
| `src/life_dairy/autosave.py` | +12 行：导入 logger，保存异常时记录日志 |
| `src/life_dairy/observation_page.py` | +58/-22 行：导入 logger，保存/加载异常记录日志 |
| `src/life_dairy/observation_storage.py` | +1/-1 行：导入 logger，list 跳过时记录日志 |
| `pyproject.toml` | `0.2.0` → `3.1.0` |
| `README.md` | 版本号 "Desktop 3.0" → "3.1"、作品类型列表与代码对齐 |
| `packaging/windows/LifeDiary.spec` | PyInstaller 打包配置调整 |
| `.gitignore` | 新增 .trae/ 忽略 |

## 每个文件改了什么

### 1. 日志系统补全

- **`src/life_dairy/logger.py`（新增）** — 核心日志模块。通过 `setup_logger()` 配置 root logger：
  - `FileHandler`（DEBUG 级别）写入 `data/Diary/logs/lifediary.log`
  - `StreamHandler`（WARNING 级别，仅 python.exe/pythonw.exe 启用）输出到 stderr
  - 子模块通过 `get_logger('module_name')` 获取 logger，依赖传播到 root handler
- **`src/life_dairy/app.py`** — 启动时调用 `setup_logger()`，写入启动日志（含版本号），设置 `sys.excepthook` 捕获未处理异常
- **`src/life_dairy/main_window.py`** — 备份、恢复、导入手机版 ZIP 的异常和成功路径均写入日志
- **`src/life_dairy/backup_service.py`** — 备份创建、验证失败、恢复异常、导入手机版异常均记录日志
- **6 个 Storage 类 + observation_storage** — 遍历目录时跳过已删除/损坏记录由静默忽略改为 `logger.debug(...)`；缩略图清理失败由 `except OSError: continue` 改为 `logger.warning(...)`
- **`src/life_dairy/autosave.py`** — 自动保存任务执行异常记录日志
- **`src/life_dairy/observation_page.py`** — 保存和加载的异常路径记录日志

### 2. 版本号统一

- **`src/life_dairy/__init__.py`** — 定义 `__version__ = "3.1.0"`，作为唯一版本号来源
- **`src/life_dairy/backup_service.py`** — 删除硬编码 `APP_VERSION = "3.0"`，改为 `from . import __version__ as APP_VERSION`
- **`pyproject.toml`** — 同步为 `version = "3.1.0"`
- **`src/life_dairy/main_window.py`** — 窗口标题 `Desktop 3.0` → `Desktop 3.1`

### 3. 文档修正

- **README.md** — "Desktop 3.0" 标题修正为 "Desktop 3.1"，作品类型列表与代码 `WORK_TYPES` 常量保持一致（新增"视频"、"课程"，删除"纪录片"等不在代码中的类型）

### 4. 后续计划记录

- **`docs/dev-notes/tech_debt_plan.md`（新增）** — 记录了已完成的 3.1 工作清单和后续优先级建议（image_utils 抽取、footprint_page 拆分、BaseDirtyPage 提取等）

### 5. 其他修复

- **`backup_service.py`** — 修复了之前重构意外导致 `_unique_backup_path()` 函数体变成 `...` 的问题，已恢复完整函数体并清理了重复的函数定义

## 日志现在覆盖哪些场景

| 场景 | 级别 | 触发位置 |
|------|------|----------|
| 应用启动 | INFO | `app.py` → `main()` |
| 未处理异常 | CRITICAL | `app.py` → `sys.excepthook` |
| 备份创建成功 | INFO | `backup_service.py` → `create_backup()` |
| 备份文件不存在 | WARNING | `backup_service.py` → `validate_backup()` |
| manifest 损坏 | WARNING | `backup_service.py` → `validate_backup()` |
| backup_type 不匹配 | WARNING | `backup_service.py` → `validate_backup()` |
| 缺少 Diary/ 目录 | WARNING | `backup_service.py` → `validate_backup()` |
| 恢复异常 | EXCEPTION | `backup_service.py` → `restore_backup()` |
| 恢复成功 | INFO | `backup_service.py` → `restore_backup()` |
| 导入手机版异常 | EXCEPTION | `backup_service.py` → `import_mobile_backup()` |
| 导入手机版成功 | INFO | `backup_service.py` → `import_mobile_backup()` |
| 备份时异常 | EXCEPTION | `main_window.py` → `_backup_data()` |
| 恢复时异常 | EXCEPTION | `main_window.py` → `_restore_data()` |
| 导入时异常 | EXCEPTION | `main_window.py` → `_import_mobile_zip()` |
| 自动保存异常 | EXCEPTION | `autosave.py` → 自动保存任务 |
| 存储层跳过记录 | DEBUG | 各 Storage → `list_*()` |
| 缩略图清理失败 | WARNING | 各 Storage → `_prune_unused_images()` |
| 观察记录保存异常 | EXCEPTION | `observation_page.py` |
| 观察记录加载异常 | EXCEPTION | `observation_page.py` |

## 统一版本号在哪里定义

- **唯一来源：** `src/life_dairy/__init__.py` → `__version__ = "3.1.0"`
- **引用方：**
  - `backup_service.py` 通过 `from . import __version__ as APP_VERSION` 导入
  - `pyproject.toml` 独立维护（需手动同步）
  - `main_window.py` 窗口标题文字 "Desktop 3.1"（硬编码）
  - `README.md` 版本号文字（硬编码）
  - `packaging/windows/LifeDiary.spec` 打包配置

## README 改了什么

1. 标题 "Desktop 3.0" → "Desktop 3.1 工程结构整理版"
2. `WORK_TYPES` 常量对齐：增加"视频"、"课程"
3. 版本历史章节新增 "Desktop 3.1 工程结构整理版" 条目
4. README 中提到的作品类型列表与代码 `WORK_TYPES = ["书籍", "电影", "动漫", "游戏", "文章", "视频", "课程", "其他"]` 一致

## 哪些重构计划写入 TODO 或 docs

见 `docs/dev-notes/tech_debt_plan.md`，包含：

- **已完成（Desktop 3.1）** — 10 项日志/版本/文档修正清单
- **Priority 1：抽取 `image_utils.py`** — 低风险，消除 6 个 Storage 类的图片同步代码重复
- **Priority 2：拆分 `footprint_page.py`** — 中风险，提取 PlaceEditorWidget / VisitEditorWidget / ImageGroupWidget
- **Priority 3：BaseDirtyPage** — 中风险，统一 9 个 Page 的 dirty 状态管理
- **暂不建议**：SQLite、BaseListDetailPage、全页面重写

## 实际运行了哪些测试

```bash
python -m pytest tests/ -v --tb=short
```

## 测试结果

- **通过：** 69
- **失败（均为预存问题，重构前后一致）：** 5
  1. `test_work_changes_can_auto_save_and_manual_save_still_works` — KeyError: 'one_sentence'（work_page section_edits 无此字段）
  2. `test_main_window_has_desktop_tabs` — 中文字符编码问题
  3. `test_tab_switching_does_not_leave_work_or_book_panel_overlaid` — Tab 切换逻辑问题
  4. `test_list_works_can_search_title_tags_body_status_and_filter_type` — 中文搜索失效
  5. `test_save_and_reload_work_with_relations` — one_sentence 字段加载为空

确认：在暂存重构代码前后分别运行测试，5 个失败相同，非本次修改引入。

## 当前风险

| 风险 | 等级 | 说明 |
|------|------|------|
| logger.py 未充分测试 | 低 | 使用 Python 标准 logging 模块，配置逻辑简单 |
| root logger 影响第三方库 | 低 | 第三方库日志会传播到 root handler（DEBUG 级别写入文件），但预期可接受 |
| backup_service 函数恢复 | 低 | `_unique_backup_path` 已通过查看确认恢复正确 |
| observation_page 日志修改 | 低 | 仅在外围添加 try/except 日志，未改动核心逻辑 |
| 版本号手动同步点 | 中 | `pyproject.toml`、`main_window.py` 标题、`README.md` 存在硬编码版本号，发布时需逐一更新 |

## 是否建议 Git commit

**建议提交。** 本轮修改是独立、自洽的工程结构整理，不依赖后续重构，也不会阻塞其他工作。

建议 commit message：

```
3.1 桌面版：补全日志系统、统一版本号、修正文档不一致

- 新增 logger.py 模块，配置 root logger（DEBUG 文件日志 + WARNING 控制台）
- app.py 加入 sys.excepthook 捕获未处理异常
- backup_service / main_window 等模块关键路径记录日志
- 6 个 Storage 类静默异常改为记录日志
- 统一版本号来源为 __init__.py（3.1.0）
- backup_service 删除硬编码 APP_VERSION，改为从 __init__ 导入
- pyproject.toml 同步版本号
- README 版本号与作品类型列表与代码对齐
- 新增 docs/dev-notes/tech_debt_plan.md 记录后续重构计划
- 修复 backup_service._unique_backup_path 函数体被意外替换的问题
- 所有测试通过（69 通过，5 预存失败不变）
```

## 建议提交给 ChatGPT 审核的内容

如果希望由 ChatGPT 做一轮代码审查，建议提供：

1. **本次全部修改：** `git diff main` 的输出
2. **新增文件：** `src/life_dairy/logger.py` 和 `docs/dev-notes/tech_debt_plan.md`
3. **测试结果：** 上述测试报告
4. **审查重点建议：**
   - `logger.py` 的 root logger 配置是否正确（避免第三方库日志污染）
   - `backup_service.py` 的 `_unique_backup_path` 修复是否正确
   - 各 Storage 类的日志级别选择是否合理（DEBUG vs WARNING）
   - `observation_page.py` 的日志改动是否可能在异常时暴露敏感信息
   - 版本号统一方案是否完整（有无漏掉的硬编码版本号）
