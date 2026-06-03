# Desktop Legacy — 当前系统事实

> 版本：3.3.0 / 4.0（`src/life_dairy/`）
> 状态：**已归档**。不再新增 UI 功能，仅作为后端数据层被 `diary_v2.0/launcher.py` 兼容引用。

## Architecture

- **GUI**: PySide6 Widgets（QSplitter + QVBoxLayout 手写布局）
- **Data Storage**: JSON 文件系统（`data/Diary/<module>/<uuid>/<file>.json`）
- **Desktop Shell**: PySide6 + QMainWindow + QTabWidget（14 个标签页）
- **AutoSave**: AutoSaveMixin（3 秒防抖 QTimer）
- **AI**: 直接 import openai 调用 DeepSeek API

## Layout Pattern

所有 13 个可编辑页面共用同一模式：

```
QHBoxLayout → QSplitter → [ QWidget(sidebar) | QWidget(editor) ]
sidebar:    QLabel(title) + QLineEdit(search) + QComboBox(filter) + QPushButton(new) + QPushButton(delete) + QListWidget
editor:     QHBoxLayout(action buttons) + QFormLayout(fields) + QTextEdit(notes)
```

## Status Model

见 `docs/状态模型.md`。每个模块有独立的状态/类型枚举。

## Limitations

1. UI 和业务逻辑在同一进程，无法独立升级
2. 布局代码重复 13 次（无 BasePage 抽象）
3. 图片管线重复 6 次（无 image_utils 抽象）
4. 页面测试覆盖率极低（仅 NotePage 有自动化测试）
5. AI 功能直接嵌入页面代码，无法复用
