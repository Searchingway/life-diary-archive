from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .backup_service import MODULE_LABELS, count_module_records, run_data_health_check
from .ui_helpers import make_scroll_area


class DataManagerPage(QWidget):
    backup_requested = Signal()
    restore_requested = Signal()
    import_mobile_requested = Signal()
    export_desktop_requested = Signal()

    def __init__(self, data_root: Path | str, parent: QWidget | None = None):
        super().__init__(parent)
        self.data_root = Path(data_root)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("数据管理中心", content)
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.refresh_button = QPushButton("刷新", content)
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.refresh_button)

        action_group = QGroupBox("数据操作", content)
        action_layout = QHBoxLayout(action_group)
        self.backup_button = QPushButton("备份整个 data/Diary", action_group)
        self.backup_button.clicked.connect(self.backup_requested.emit)
        self.restore_button = QPushButton("恢复备份", action_group)
        self.restore_button.clicked.connect(self.restore_requested.emit)
        self.import_button = QPushButton("导入手机版 ZIP", action_group)
        self.import_button.clicked.connect(self.import_mobile_requested.emit)
        self.export_button = QPushButton("导出电脑版 ZIP", action_group)
        self.export_button.clicked.connect(self.export_desktop_requested.emit)
        self.open_folder_button = QPushButton("打开数据文件夹", action_group)
        self.open_folder_button.clicked.connect(self.open_data_folder)
        for button in (
            self.backup_button,
            self.restore_button,
            self.import_button,
            self.export_button,
            self.open_folder_button,
        ):
            action_layout.addWidget(button)
        action_layout.addStretch(1)

        path_group = QGroupBox("当前数据目录", content)
        path_layout = QVBoxLayout(path_group)
        self.path_label = QLabel(str(self.data_root), path_group)
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label)

        counts_group = QGroupBox("各模块记录数量", content)
        counts_layout = QVBoxLayout(counts_group)
        self.count_list = QListWidget(counts_group)
        counts_layout.addWidget(self.count_list)

        health_group = QGroupBox("数据健康检查", content)
        health_layout = QVBoxLayout(health_group)
        self.health_button = QPushButton("运行数据健康检查", health_group)
        self.health_button.clicked.connect(self.run_health_check)
        self.health_output = QTextEdit(health_group)
        self.health_output.setReadOnly(True)
        self.health_output.setMinimumHeight(180)
        health_layout.addWidget(self.health_button)
        health_layout.addWidget(self.health_output)

        layout.addLayout(header)
        layout.addWidget(action_group)
        layout.addWidget(path_group)
        layout.addWidget(counts_group)
        layout.addWidget(health_group, 1)
        outer.addWidget(make_scroll_area(content))

    def set_data_root(self, data_root: Path | str) -> None:
        self.data_root = Path(data_root)
        self.refresh()

    def refresh(self) -> None:
        self.path_label.setText(str(self.data_root))
        self.count_list.clear()
        counts = count_module_records(self.data_root)
        for module, label in MODULE_LABELS.items():
            self.count_list.addItem(QListWidgetItem(f"{label}：{counts.get(module, 0)} 条"))
        if self.count_list.count() == 0:
            self.count_list.addItem("暂无可统计的数据模块。")

    def run_health_check(self) -> None:
        lines = []
        for level, message in run_data_health_check(self.data_root):
            lines.append(f"[{level}] {message}")
        self.health_output.setPlainText("\n".join(lines))

    def open_data_folder(self) -> None:
        self.data_root.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.data_root.resolve())))
