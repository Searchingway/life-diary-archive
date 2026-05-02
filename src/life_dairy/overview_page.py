from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .overview import OverviewService, OverviewStats, TimelineItem
from .ui_helpers import make_scroll_area


class OverviewPage(QWidget):
    backup_requested = Signal()
    restore_requested = Signal()
    open_record_requested = Signal(str, str)

    def __init__(self, service: OverviewService, parent: QWidget | None = None):
        super().__init__(parent)
        self.service = service
        self.stat_labels: dict[str, QLabel] = {}
        self.module_list: QListWidget | None = None
        self._build_ui()
        self.refresh_overview()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("总览", content)
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.refresh_button = QPushButton("刷新总览", content)
        self.refresh_button.clicked.connect(self.refresh_overview)
        self.backup_button = QPushButton("备份数据", content)
        self.backup_button.clicked.connect(self.backup_requested.emit)
        self.restore_button = QPushButton("恢复备份", content)
        self.restore_button.clicked.connect(self.restore_requested.emit)
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(self.backup_button)
        header_row.addWidget(self.restore_button)
        header_row.addWidget(self.refresh_button)

        layout.addLayout(header_row)
        layout.addWidget(self._build_stats_group())
        layout.addWidget(self._build_module_group())
        layout.addWidget(self._build_timeline_group(), 1)
        outer.addWidget(make_scroll_area(content))

    def _build_stats_group(self) -> QWidget:
        group = QGroupBox("基础统计", self)
        grid = QGridLayout(group)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        items = [
            ("month_diary_count", "本月日记篇数"),
            ("month_diary_chars", "本月日记总字数"),
            ("month_diary_images", "本月日记图片数"),
            ("month_completed_plans", "本月完成计划数"),
            ("year_diary_count", "今年日记篇数"),
            ("year_diary_chars", "今年日记总字数"),
            ("year_diary_images", "今年日记图片数"),
            ("year_completed_plans", "今年完成计划数"),
        ]
        for index, (key, label_text) in enumerate(items):
            row = index // 4
            column = index % 4
            cell = QWidget(group)
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(10, 8, 10, 8)
            label = QLabel(label_text, cell)
            value = QLabel("0", cell)
            value.setAlignment(Qt.AlignmentFlag.AlignLeft)
            value.setStyleSheet("font-size: 24px; font-weight: 700; color: #315c3c;")
            cell_layout.addWidget(label)
            cell_layout.addWidget(value)
            self.stat_labels[key] = value
            grid.addWidget(cell, row, column)

        return group

    def _build_module_group(self) -> QWidget:
        group = QGroupBox("全模块数量与最近更新时间", self)
        layout = QVBoxLayout(group)
        self.module_list = QListWidget(group)
        self.module_list.setMaximumHeight(150)
        layout.addWidget(self.module_list)
        return group

    def _build_timeline_group(self) -> QWidget:
        group = QGroupBox("最近记录时间线", self)
        layout = QVBoxLayout(group)
        self.timeline_list = QListWidget(group)
        self.timeline_list.itemDoubleClicked.connect(self._open_selected_timeline_item)
        layout.addWidget(self.timeline_list, 1)
        return group

    def refresh_overview(self) -> None:
        stats = self.service.build_stats()
        self._fill_stats(stats)
        self._fill_timeline(self.service.build_timeline(30))
        self._show_status("总览已刷新。", 3000)

    def _fill_stats(self, stats: OverviewStats) -> None:
        for key, label in self.stat_labels.items():
            label.setText(str(getattr(stats, key)))
        if self.module_list is not None:
            self.module_list.clear()
            counts = stats.module_counts or {}
            latest = stats.latest_updates or {}
            for name, count in counts.items():
                latest_text = latest.get(name, "")[:19].replace("T", " ") or "暂无"
                self.module_list.addItem(f"{name}：{count} 条，最近更新 {latest_text}")
            if self.module_list.count() == 0:
                self.module_list.addItem("暂无模块统计。")

    def _fill_timeline(self, items: list[TimelineItem]) -> None:
        self.timeline_list.clear()
        for item in items:
            lines = [
                f"{item.date}  【{item.record_type}】{item.title}",
            ]
            if item.summary:
                lines.append(f"摘要：{item.summary}")
            if item.status:
                lines.append(f"状态：{item.status}")
            if item.image_count:
                lines.append(f"图片：{item.image_count} 张")
            list_item = QListWidgetItem("\n".join(lines))
            list_item.setData(Qt.ItemDataRole.UserRole, (item.source_module, item.record_id))
            list_item.setToolTip(item.source_module)
            self.timeline_list.addItem(list_item)

    def _open_selected_timeline_item(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        source_module, record_id = data
        self.open_record_requested.emit(str(source_module), str(record_id))

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
