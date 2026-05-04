# 技术债与重构计划

## 已完成（Desktop 3.1）

- [x] 日志系统补全：app.py 加入 sys.excepthook
- [x] 日志系统补全：backup_service.py 关键操作加入 logger.info / logger.exception
- [x] 日志系统补全：main_window.py 备份/恢复/导入异常加入 logger.exception
- [x] 日志系统补全：storage 层文件读写失败时记录 logger.warning / logger.debug
- [x] 日志系统补全：所有 storage 的 except OSError: continue/ pass 改为记录日志
- [x] 版本号统一：__init__.py 定义 __version__ = "3.1.0"
- [x] 版本号统一：backup_service.py 从 __init__.py 导入版本号
- [x] 版本号统一：pyproject.toml 同步为 3.1.0
- [x] 文档修正：README 中作品类型与代码 WORK_TYPES 保持一致
- [x] 文档修正：README 版本号同步更新

## 后续重构计划（按优先级排列）

### 1. 抽取 image_utils.py（低风险，高收益）

当前 6 个 Storage 类（DiaryStorage、FootprintStorage、BookStorage、LessonStorage、SelfAnalysisStorage、WorkStorage）各自重复实现了：
- `_sync_images()`
- `_copy_image()`
- `_unique_name()`
- `_prune_unused_images()`

建议抽取到 `src/life_dairy/image_utils.py`，统一图片同步逻辑。

**预计工作量：** 1 天
**风险：** 低（纯 internal 重构）

### 2. 拆分 footprint_page.py 的超长 UI 构造方法（中风险）

`footprint_page.py`（1063 行）的 `_build_editor()`（~130 行）在一个方法中构建了地点档案、日期关联、双层图片管理等全部 UI 布局。

建议方案：
- 提取 `PlaceEditorWidget`（地点档案编辑器）
- 提取 `VisitEditorWidget`（日期关联编辑器）
- 提取 `ImageGroupWidget`（通用图片管理组）

**预计工作量：** 2 天
**风险：** 中（UI 组件重构需小心信号槽连接）

### 3. 考虑 BaseDirtyPage / BaseAutoSavePage（中风险）

当前 9 个 Page 类重复实现了相同的 dirty 状态管理和自动保存模式代码：
- `has_unsaved_changes()`
- `maybe_finish_pending_changes()`
- `_mark_dirty()` / `_set_dirty()`
- `_show_status()`

建议提取一个基类或增强 AutoSaveMixin。

**预计工作量：** 2-3 天
**风险：** 中（需协调所有 Page 子类）

### 4. 暂不建议迁移 SQLite

理由：
- JSON 文件存储满足当前单用户本地使用场景
- 迁移 SQLite 需要重写全部 10 个 Storage 类
- 需要处理现有用户数据的迁移
- 收益在当前阶段不明显

### 5. 暂不建议一次性抽 BaseListDetailPage

理由：
- 虽然 9 个 Page 类有相同的列表-详情模式，但每个页面的筛选条件和编辑器布局差异较大
- 强行抽取会导致大量的条件分支或模板方法，反而降低可读性
- 建议先完成第 3 项（BaseDirtyPage），再评估是否需要进一步的页面基类抽取

### 6. 暂不建议重写所有 Page

理由：
- 当前架构虽然不够优雅，但功能稳定
- 用户数据完整，测试覆盖基本可用
- 大规模重写风险高，收益不确定
