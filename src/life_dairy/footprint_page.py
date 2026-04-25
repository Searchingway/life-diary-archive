from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, QSize, QSignalBlocker, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .exchange import ExchangePackageExporter
from .footprint_storage import FootprintStorage
from .models import FootprintImageDraft, FootprintPlace, FootprintVisit
from .storage import DiaryStorage
from .ui_helpers import make_scroll_area


class FootprintPage(QWidget):
    dirty_state_changed = Signal(bool)
    open_diary_requested = Signal(str)

    def __init__(
        self,
        storage: FootprintStorage,
        diary_storage: DiaryStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.diary_storage = diary_storage
        self.current_place: FootprintPlace | None = None
        self.current_visit_id: str | None = None
        self.place_image_items: list[FootprintImageDraft] = []
        self.visit_image_items: dict[str, list[FootprintImageDraft]] = {}
        self.is_dirty = False
        self._is_loading_form = False
        self._is_loading_place_image_details = False
        self._is_loading_visit_image_details = False
        self._build_ui()
        self.refresh_place_list()
        if self.place_list.count() > 0:
            self.place_list.setCurrentRow(0)
        else:
            self.new_place()

    def has_unsaved_changes(self) -> bool:
        return self.is_dirty

    def maybe_finish_pending_changes(self) -> bool:
        return self._maybe_keep_changes()

    def open_first_place_for_date(self, target_date: str) -> bool | None:
        matches = self.storage.list_place_visits_by_date(target_date)
        if not matches:
            return False
        if not self._maybe_keep_changes():
            return None

        place, visit = matches[0]
        blocker = QSignalBlocker(self.search_input)
        self.search_input.clear()
        del blocker
        self.refresh_place_list(select_id=place.id)
        self._open_place_by_id(
            place.id,
            select_visit_id=visit.id,
            status_message=f"已定位到 {target_date} 对应的地点足迹。",
        )
        return True

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_editor())
        splitter.setSizes([300, 900])

        layout.addWidget(make_scroll_area(splitter))

    def _build_sidebar(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("地点足迹", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索地点 / 简介 / 日期 / 感悟")
        self.search_input.textChanged.connect(self.refresh_place_list)

        self.new_place_button = QPushButton("新建地点足迹", widget)
        self.new_place_button.clicked.connect(self.new_place)

        self.delete_place_button = QPushButton("删除当前地点足迹", widget)
        self.delete_place_button.clicked.connect(self.delete_current_place)

        self.export_package_button = QPushButton("导出足迹压缩包", widget)
        self.export_package_button.clicked.connect(self.export_footprint_package)

        self.place_list = QListWidget(widget)
        self.place_list.currentItemChanged.connect(self._on_current_place_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.new_place_button)
        layout.addWidget(self.delete_place_button)
        layout.addWidget(self.export_package_button)
        layout.addWidget(self.place_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_place)

        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_place)

        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addStretch(1)

        place_group = QGroupBox("地点档案", widget)
        place_layout = QVBoxLayout(place_group)

        place_form = QFormLayout()
        self.place_name_input = QLineEdit(place_group)
        self.place_name_input.setPlaceholderText("例如：松花江畔、青秀山、老城区书店")
        self.place_name_input.textChanged.connect(self._on_place_name_changed)

        place_form.addRow("地点主题", self.place_name_input)
        place_layout.addLayout(place_form)

        summary_label = QLabel("地点粗略描述", place_group)
        self.place_summary_edit = QTextEdit(place_group)
        self.place_summary_edit.setPlaceholderText("这里写地点本身的描述，例如环境、印象、适合做什么、为什么值得记住。")
        self.place_summary_edit.setMinimumHeight(130)
        self.place_summary_edit.textChanged.connect(self._on_place_summary_changed)

        place_note = QLabel("先把地点本身建成一个档案，下面再给这个地点添加多个日期关联。", place_group)
        place_note.setWordWrap(True)
        place_note.setStyleSheet("color: #666666;")

        place_layout.addWidget(summary_label)
        place_layout.addWidget(self.place_summary_edit)
        place_layout.addWidget(place_note)
        place_layout.addWidget(self._build_place_image_group())

        visit_group = QGroupBox("日期关联记录", widget)
        visit_group.setMinimumHeight(520)
        visit_layout = QVBoxLayout(visit_group)

        visit_action_row = QHBoxLayout()
        self.new_visit_button = QPushButton("新增日期关联", visit_group)
        self.new_visit_button.clicked.connect(self.new_visit)

        self.delete_visit_button = QPushButton("删除当前日期关联", visit_group)
        self.delete_visit_button.clicked.connect(self.delete_current_visit)

        self.open_diary_button = QPushButton("打开当日日记", visit_group)
        self.open_diary_button.clicked.connect(self._emit_open_diary_requested)

        visit_action_row.addWidget(self.new_visit_button)
        visit_action_row.addWidget(self.delete_visit_button)
        visit_action_row.addWidget(self.open_diary_button)
        visit_action_row.addStretch(1)

        visit_splitter = QSplitter(Qt.Orientation.Horizontal, visit_group)

        visit_list_panel = QWidget(visit_group)
        visit_list_layout = QVBoxLayout(visit_list_panel)
        visit_list_layout.setContentsMargins(0, 0, 0, 0)
        visit_list_layout.setSpacing(8)

        visit_list_title = QLabel("这个地点关联的日期", visit_list_panel)
        self.visit_list = QListWidget(visit_list_panel)
        self.visit_list.currentItemChanged.connect(self._on_current_visit_item_changed)

        visit_list_layout.addWidget(visit_list_title)
        visit_list_layout.addWidget(self.visit_list, 1)

        visit_editor_panel = QWidget(visit_group)
        visit_editor_layout = QVBoxLayout(visit_editor_panel)
        visit_editor_layout.setContentsMargins(0, 0, 0, 0)
        visit_editor_layout.setSpacing(10)

        self.visit_note_label = QLabel("请选择一个日期关联，或者先新增一个日期关联。", visit_editor_panel)
        self.visit_note_label.setWordWrap(True)
        self.visit_note_label.setStyleSheet("color: #666666;")

        visit_form = QFormLayout()
        self.visit_date_edit = QDateEdit(visit_editor_panel)
        self.visit_date_edit.setCalendarPopup(True)
        self.visit_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.visit_date_edit.dateChanged.connect(self._on_visit_date_changed)

        visit_form.addRow("关联日期", self.visit_date_edit)

        relation_row = QHBoxLayout()
        self.diary_hint_label = QLabel("当日日记：0 篇", visit_editor_panel)
        relation_row.addWidget(self.diary_hint_label)
        relation_row.addStretch(1)

        thought_label = QLabel("这一天的感悟", visit_editor_panel)
        self.visit_thought_edit = QTextEdit(visit_editor_panel)
        self.visit_thought_edit.setPlaceholderText("这里写这次到这个地方时，当天的感受、发生的事情、当时的心情。")
        self.visit_thought_edit.setMinimumHeight(180)
        self.visit_thought_edit.textChanged.connect(self._on_visit_thought_changed)

        visit_editor_layout.addWidget(self.visit_note_label)
        visit_editor_layout.addLayout(visit_form)
        visit_editor_layout.addLayout(relation_row)
        visit_editor_layout.addWidget(thought_label)
        visit_editor_layout.addWidget(self.visit_thought_edit, 1)
        visit_editor_layout.addWidget(self._build_visit_image_group())

        visit_splitter.addWidget(visit_list_panel)
        visit_splitter.addWidget(visit_editor_panel)
        visit_splitter.setSizes([220, 700])

        visit_layout.addLayout(visit_action_row)
        visit_layout.addWidget(visit_splitter, 1)

        right_splitter = QSplitter(Qt.Orientation.Vertical, widget)
        right_splitter.addWidget(place_group)
        right_splitter.addWidget(visit_group)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setStretchFactor(0, 0)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([360, 520])

        layout.addLayout(action_row)
        layout.addWidget(right_splitter, 1)
        return widget

    def _build_place_image_group(self) -> QWidget:
        group = QGroupBox("地点图片", self)
        layout = QHBoxLayout(group)

        left = QVBoxLayout()
        self.place_image_list = QListWidget(group)
        self.place_image_list.currentItemChanged.connect(self._on_place_image_selection_changed)

        button_row = QHBoxLayout()
        self.add_place_image_button = QPushButton("添加地点图片", group)
        self.add_place_image_button.clicked.connect(self.add_place_images)
        self.open_place_image_button = QPushButton("打开所选图片", group)
        self.open_place_image_button.clicked.connect(self.open_selected_place_image)
        self.remove_place_image_button = QPushButton("移除所选图片", group)
        self.remove_place_image_button.clicked.connect(self.remove_selected_place_image)

        button_row.addWidget(self.add_place_image_button)
        button_row.addWidget(self.open_place_image_button)
        button_row.addWidget(self.remove_place_image_button)

        self.place_image_label_input = QLineEdit(group)
        self.place_image_label_input.setPlaceholderText("地点图片备注（可选）")
        self.place_image_label_input.textChanged.connect(self._update_selected_place_image_label)

        left.addWidget(self.place_image_list, 1)
        left.addLayout(button_row)
        left.addWidget(self.place_image_label_input)

        self.place_image_preview = QLabel("未选择图片", group)
        self.place_image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.place_image_preview.setMinimumSize(220, 160)
        self.place_image_preview.setStyleSheet(
            "border: 1px solid #cccccc; background: #fafafa; color: #666666;",
        )

        layout.addLayout(left, 2)
        layout.addWidget(self.place_image_preview, 1)
        return group

    def _build_visit_image_group(self) -> QWidget:
        group = QGroupBox("这一天的图片", self)
        layout = QHBoxLayout(group)

        left = QVBoxLayout()
        self.visit_image_list = QListWidget(group)
        self.visit_image_list.currentItemChanged.connect(self._on_visit_image_selection_changed)

        button_row = QHBoxLayout()
        self.add_visit_image_button = QPushButton("添加当天图片", group)
        self.add_visit_image_button.clicked.connect(self.add_visit_images)
        self.open_visit_image_button = QPushButton("打开所选图片", group)
        self.open_visit_image_button.clicked.connect(self.open_selected_visit_image)
        self.remove_visit_image_button = QPushButton("移除所选图片", group)
        self.remove_visit_image_button.clicked.connect(self.remove_selected_visit_image)

        button_row.addWidget(self.add_visit_image_button)
        button_row.addWidget(self.open_visit_image_button)
        button_row.addWidget(self.remove_visit_image_button)

        self.visit_image_label_input = QLineEdit(group)
        self.visit_image_label_input.setPlaceholderText("当天图片备注（可选）")
        self.visit_image_label_input.textChanged.connect(self._update_selected_visit_image_label)

        left.addWidget(self.visit_image_list, 1)
        left.addLayout(button_row)
        left.addWidget(self.visit_image_label_input)

        self.visit_image_preview = QLabel("未选择图片", group)
        self.visit_image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visit_image_preview.setMinimumSize(220, 160)
        self.visit_image_preview.setStyleSheet(
            "border: 1px solid #cccccc; background: #fafafa; color: #666666;",
        )

        layout.addLayout(left, 2)
        layout.addWidget(self.visit_image_preview, 1)
        return group

    def refresh_place_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id
        if current_id is None and self.current_place is not None:
            current_id = self.current_place.id

        query = self.search_input.text() if hasattr(self, "search_input") else ""
        blocker = QSignalBlocker(self.place_list)
        self.place_list.clear()

        target_row = -1
        for row, place in enumerate(self.storage.list_places(query)):
            item = QListWidgetItem(self._build_place_list_text(place))
            item.setData(Qt.ItemDataRole.UserRole, place.id)
            item.setToolTip(place.summary[:150] or place.display_title)
            item.setSizeHint(QSize(0, 46))
            self.place_list.addItem(item)
            if current_id and place.id == current_id:
                target_row = row

        if target_row >= 0:
            self.place_list.setCurrentRow(target_row)
        del blocker

    def new_place(self) -> None:
        if not self._maybe_keep_changes():
            return

        self._fill_place(self.storage.create_empty_place(), select_visit_id=None)
        self.place_list.blockSignals(True)
        self.place_list.clearSelection()
        self.place_list.blockSignals(False)
        self._show_status("已创建新的地点足迹草稿。", 3000)

    def save_place(self) -> None:
        if self.current_place is None:
            self.current_place = self.storage.create_empty_place()

        try:
            saved = self.storage.save_place(
                self.current_place,
                self.place_image_items,
                self.visit_image_items,
            )
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存地点足迹时出错：\n{exc}")
            return

        selected_visit_id = self.current_visit_id
        self._fill_place(saved, select_visit_id=selected_visit_id)
        self.refresh_place_list(select_id=saved.id)
        self._show_status("已保存地点足迹到本地。", 3000)

    def reload_current_place(self) -> None:
        if self.current_place is None:
            return

        if self.is_dirty:
            reply = QMessageBox.question(
                self,
                "恢复确认",
                "当前有未保存修改，恢复后会丢失这些改动。是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if self.current_place.id and self.storage.footprint_dir(self.current_place.id).exists():
            try:
                place = self.storage.load_place(self.current_place.id)
            except Exception as exc:
                QMessageBox.critical(self, "读取失败", f"恢复已保存内容时出错：\n{exc}")
                return
            self._fill_place(place, select_visit_id=self.current_visit_id)
            self.refresh_place_list(select_id=place.id)
            self._show_status("已恢复到上次保存的地点足迹内容。", 3000)

    def delete_current_place(self) -> None:
        if self.current_place is None:
            return

        if not self.storage.footprint_dir(self.current_place.id).exists():
            reply = QMessageBox.question(
                self,
                "放弃草稿",
                "这个地点足迹草稿还没有保存，确定要放弃吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._discard_current_draft("已放弃未保存的地点足迹草稿。")
            return

        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定要删除这个地点足迹吗？\n\n{self.current_place.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        place_id = self.current_place.id
        try:
            self.storage.delete_place(place_id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除地点足迹时出错：\n{exc}")
            return

        self.current_place = None
        self.current_visit_id = None
        self.place_image_items = []
        self.visit_image_items = {}
        self._set_dirty(False)
        self.refresh_place_list()

        if self.place_list.count() > 0:
            self.place_list.setCurrentRow(0)
        else:
            self.new_place()

        self._show_status("已删除当前地点足迹。", 3000)

    def export_footprint_package(self) -> None:
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "选择足迹压缩包导出目录",
            str((self.storage.root_dir / "exports").resolve()),
        )
        if not export_dir:
            return

        try:
            zip_path = ExchangePackageExporter(self.storage.root_dir).export_module("footprint", export_dir)
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"导出足迹压缩包时出错：\n{exc}")
            return

        QMessageBox.information(self, "导出完成", f"足迹压缩包已生成：\n\n{zip_path}")
        self._show_status("已导出足迹压缩包。", 5000)

    def new_visit(self) -> None:
        if self.current_place is None:
            self._fill_place(self.storage.create_empty_place(), select_visit_id=None)

        if self.current_place is None:
            return

        visit = self.storage.create_empty_visit()
        self.current_place.visits.append(visit)
        self.visit_image_items[visit.id] = []
        self._refresh_visit_list(select_visit_id=visit.id)
        self._mark_dirty()
        self._show_status("已为当前地点新增一个日期关联。", 3000)

    def delete_current_visit(self) -> None:
        visit = self._current_visit()
        if visit is None or self.current_place is None:
            return

        reply = QMessageBox.question(
            self,
            "删除日期关联",
            f"确定要删除这个日期关联吗？\n\n{visit.date or '未设日期'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        remaining = [item for item in self.current_place.visits if item.id != visit.id]
        self.current_place.visits = remaining
        self.visit_image_items.pop(visit.id, None)

        next_visit_id = remaining[min(self.visit_list.currentRow(), len(remaining) - 1)].id if remaining else None
        self._refresh_visit_list(select_visit_id=next_visit_id)
        self._mark_dirty()
        self._show_status("已移除这个日期关联，保存后生效。", 3000)

    def add_place_images(self) -> None:
        added_count = self._add_images(self.place_image_items)
        if added_count == 0:
            return

        self._refresh_place_image_list(select_row=len(self.place_image_items) - 1)
        self._mark_dirty()
        self._show_status(f"已加入 {added_count} 张地点图片，保存后生效。", 3000)

    def add_visit_images(self) -> None:
        visit = self._current_visit()
        if visit is None:
            QMessageBox.information(self, "先选日期关联", "请先新增或选择一个日期关联。")
            return

        items = self._current_visit_image_items()
        added_count = self._add_images(items)
        if added_count == 0:
            return

        self._refresh_visit_image_list(select_row=len(items) - 1)
        self._mark_dirty()
        self._show_status(f"已加入 {added_count} 张当天图片，保存后生效。", 3000)

    def remove_selected_place_image(self) -> None:
        current_row = self.place_image_list.currentRow()
        if current_row < 0:
            return

        del self.place_image_items[current_row]
        next_row = min(current_row, len(self.place_image_items) - 1)
        self._refresh_place_image_list(select_row=next_row if next_row >= 0 else None)
        self._mark_dirty()
        self._show_status("已移除所选地点图片，保存后生效。", 3000)

    def remove_selected_visit_image(self) -> None:
        visit_items = self._current_visit_image_items()
        current_row = self.visit_image_list.currentRow()
        if current_row < 0 or current_row >= len(visit_items):
            return

        del visit_items[current_row]
        next_row = min(current_row, len(visit_items) - 1)
        self._refresh_visit_image_list(select_row=next_row if next_row >= 0 else None)
        self._mark_dirty()
        self._show_status("已移除所选当天图片，保存后生效。", 3000)

    def open_selected_place_image(self) -> None:
        self._open_image(self._current_place_image_path())

    def open_selected_visit_image(self) -> None:
        self._open_image(self._current_visit_image_path())

    def _fill_place(self, place: FootprintPlace, select_visit_id: str | None) -> None:
        self._is_loading_form = True
        self.current_place = place
        self.place_image_items = [
            FootprintImageDraft(
                source_path=self.storage.resolve_place_image_path(place.id, image.file_name),
                label=image.label,
            )
            for image in place.images
        ]
        self.visit_image_items = {
            visit.id: [
                FootprintImageDraft(
                    source_path=self.storage.resolve_visit_image_path(place.id, visit.id, image.file_name),
                    label=image.label,
                )
                for image in visit.images
            ]
            for visit in place.visits
        }

        try:
            self.place_name_input.setText(place.place_name)
            self.place_summary_edit.setPlainText(place.summary)
            self._refresh_place_image_list()
            self._refresh_visit_list(select_visit_id=select_visit_id)
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _open_place_by_id(
        self,
        place_id: str,
        select_visit_id: str | None = None,
        status_message: str | None = None,
    ) -> None:
        try:
            place = self.storage.load_place(place_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取地点足迹时出错：\n{exc}")
            return

        self._fill_place(place, select_visit_id=select_visit_id)
        self.refresh_place_list(select_id=place.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_place = None
        self.current_visit_id = None
        self.place_image_items = []
        self.visit_image_items = {}
        self._set_dirty(False)
        self.refresh_place_list()

        if self.place_list.count() > 0:
            self.place_list.setCurrentRow(0)
        else:
            self.new_place()

        self._show_status(status_message, 3000)

    def _on_current_place_item_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.place_list)
            self.place_list.setCurrentItem(previous)
            del blocker
            return

        place_id = current.data(Qt.ItemDataRole.UserRole)
        if self.current_place is not None and self.current_place.id == place_id:
            return
        self._open_place_by_id(place_id, status_message="已重新打开这个地点足迹。")

    def _refresh_visit_list(self, select_visit_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.visit_list)
        self.visit_list.clear()

        visits = self.current_place.visits if self.current_place is not None else []
        target_row = -1
        for row, visit in enumerate(visits):
            item = QListWidgetItem(self._build_visit_list_text(visit))
            item.setData(Qt.ItemDataRole.UserRole, visit.id)
            item.setToolTip(visit.thought[:150] or visit.display_title)
            item.setSizeHint(QSize(0, 42))
            self.visit_list.addItem(item)
            if select_visit_id and visit.id == select_visit_id:
                target_row = row

        if target_row < 0 and visits:
            target_row = 0
        if target_row >= 0:
            self.visit_list.setCurrentRow(target_row)
            self.current_visit_id = visits[target_row].id
        else:
            self.current_visit_id = None
        del blocker
        self._load_current_visit_into_editor()

    def _on_current_visit_item_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            self.current_visit_id = None
            self._load_current_visit_into_editor()
            return

        self.current_visit_id = current.data(Qt.ItemDataRole.UserRole)
        self._load_current_visit_into_editor()

    def _load_current_visit_into_editor(self) -> None:
        visit = self._current_visit()
        self._is_loading_form = True
        try:
            enabled = visit is not None
            self.delete_visit_button.setEnabled(enabled)
            self.open_diary_button.setEnabled(enabled)
            self.visit_date_edit.setEnabled(enabled)
            self.visit_thought_edit.setEnabled(enabled)
            self.add_visit_image_button.setEnabled(enabled)
            self.open_visit_image_button.setEnabled(enabled)
            self.remove_visit_image_button.setEnabled(enabled)
            self.visit_image_label_input.setEnabled(enabled)
            self.visit_image_list.setEnabled(enabled)

            if visit is None:
                self.visit_note_label.setText("请选择一个日期关联，或者先新增一个日期关联。")
                self.visit_date_edit.setDate(QDate.currentDate())
                self.visit_thought_edit.clear()
                self.diary_hint_label.setText("当日日记：0 篇")
                self._refresh_visit_image_list(select_row=None)
                return

            self.visit_note_label.setText("这一块记录的是“这个地点在某一天发生了什么”。")
            date_value = QDate.fromString(visit.date, "yyyy-MM-dd")
            if not date_value.isValid():
                date_value = QDate.currentDate()
            self.visit_date_edit.setDate(date_value)
            self.visit_thought_edit.setPlainText(visit.thought)
            self._refresh_diary_relation()
            self._refresh_visit_image_list()
        finally:
            self._is_loading_form = False

    def _current_visit(self) -> FootprintVisit | None:
        if self.current_place is None or not self.current_visit_id:
            return None
        for visit in self.current_place.visits:
            if visit.id == self.current_visit_id:
                return visit
        return None

    def _current_visit_image_items(self) -> list[FootprintImageDraft]:
        if not self.current_visit_id:
            return []
        return self.visit_image_items.setdefault(self.current_visit_id, [])

    def _on_place_name_changed(self, text: str) -> None:
        if self._is_loading_form or self.current_place is None:
            return
        self.current_place.place_name = text.strip()
        self._mark_dirty()

    def _on_place_summary_changed(self) -> None:
        if self._is_loading_form or self.current_place is None:
            return
        self.current_place.summary = self.place_summary_edit.toPlainText()
        self._mark_dirty()

    def _on_visit_date_changed(self, *_args) -> None:
        if self._is_loading_form:
            return
        visit = self._current_visit()
        if visit is None:
            return

        visit.date = self.visit_date_edit.date().toString("yyyy-MM-dd")
        self._auto_assign_related_entry(visit)
        self._refresh_visit_list(select_visit_id=visit.id)
        self._refresh_diary_relation()
        self._mark_dirty()

    def _on_visit_thought_changed(self) -> None:
        if self._is_loading_form:
            return
        visit = self._current_visit()
        if visit is None:
            return
        visit.thought = self.visit_thought_edit.toPlainText()
        self._mark_dirty()

    def _refresh_diary_relation(self) -> None:
        visit = self._current_visit()
        if visit is None:
            self.diary_hint_label.setText("当日日记：0 篇")
            self.open_diary_button.setEnabled(False)
            return

        target_date = visit.date
        count = len(self.diary_storage.list_entries_by_date(target_date))
        self.diary_hint_label.setText(f"当日日记：{count} 篇")
        self.open_diary_button.setEnabled(count > 0)

    def _auto_assign_related_entry(self, visit: FootprintVisit) -> None:
        related_entries = self.diary_storage.list_entries_by_date(visit.date)
        if len(related_entries) == 1:
            visit.related_entry_id = related_entries[0].id
            return
        if visit.related_entry_id:
            available_ids = {item.id for item in related_entries}
            if visit.related_entry_id in available_ids:
                return
        visit.related_entry_id = ""

    def _emit_open_diary_requested(self) -> None:
        visit = self._current_visit()
        if visit is None:
            return
        self.open_diary_requested.emit(visit.date)

    def _on_place_image_selection_changed(self, *_args) -> None:
        self._update_place_image_preview()
        row = self.place_image_list.currentRow()

        self._is_loading_place_image_details = True
        try:
            if row < 0 or row >= len(self.place_image_items):
                self.place_image_label_input.clear()
                return
            self.place_image_label_input.setText(self.place_image_items[row].label)
        finally:
            self._is_loading_place_image_details = False

    def _on_visit_image_selection_changed(self, *_args) -> None:
        self._update_visit_image_preview()
        items = self._current_visit_image_items()
        row = self.visit_image_list.currentRow()

        self._is_loading_visit_image_details = True
        try:
            if row < 0 or row >= len(items):
                self.visit_image_label_input.clear()
                return
            self.visit_image_label_input.setText(items[row].label)
        finally:
            self._is_loading_visit_image_details = False

    def _update_selected_place_image_label(self, text: str) -> None:
        if self._is_loading_place_image_details:
            return

        row = self.place_image_list.currentRow()
        if row < 0 or row >= len(self.place_image_items):
            return

        normalized = text.strip()
        if self.place_image_items[row].label == normalized:
            return

        self.place_image_items[row].label = normalized
        self._refresh_place_image_list(select_row=row)
        self._mark_dirty()

    def _update_selected_visit_image_label(self, text: str) -> None:
        if self._is_loading_visit_image_details:
            return

        items = self._current_visit_image_items()
        row = self.visit_image_list.currentRow()
        if row < 0 or row >= len(items):
            return

        normalized = text.strip()
        if items[row].label == normalized:
            return

        items[row].label = normalized
        self._refresh_visit_image_list(select_row=row)
        self._mark_dirty()

    def _add_images(self, target_items: list[FootprintImageDraft]) -> int:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not files:
            return 0

        existing: set[str] = set()
        for image_item in target_items:
            try:
                existing.add(str(image_item.source_path.resolve()).lower())
            except FileNotFoundError:
                continue

        added_count = 0
        for file_path in files:
            path = Path(file_path)
            try:
                normalized = str(path.resolve()).lower()
            except FileNotFoundError:
                continue
            if normalized in existing:
                continue
            target_items.append(FootprintImageDraft(source_path=path, label=""))
            existing.add(normalized)
            added_count += 1
        return added_count

    def _refresh_place_image_list(self, select_row: int | None = 0) -> None:
        self._refresh_image_list(
            self.place_image_list,
            self.place_image_items,
            self._is_saved_place_image,
            select_row,
        )
        self._on_place_image_selection_changed()

    def _refresh_visit_image_list(self, select_row: int | None = 0) -> None:
        self._refresh_image_list(
            self.visit_image_list,
            self._current_visit_image_items(),
            self._is_saved_visit_image,
            select_row,
        )
        self._on_visit_image_selection_changed()

    def _refresh_image_list(
        self,
        widget: QListWidget,
        image_items: list[FootprintImageDraft],
        is_saved_checker,
        select_row: int | None,
    ) -> None:
        blocker = QSignalBlocker(widget)
        widget.clear()

        for index, image_item in enumerate(image_items, start=1):
            label = image_item.label.strip() or f"图片 {index}"
            if not is_saved_checker(image_item.source_path):
                label = f"{label} (待保存)"
            item = QListWidgetItem(label)
            item.setToolTip(str(image_item.source_path))
            widget.addItem(item)

        if select_row is not None and 0 <= select_row < widget.count():
            widget.setCurrentRow(select_row)

        del blocker

    def _is_saved_place_image(self, image_path: Path) -> bool:
        if self.current_place is None:
            return False
        return image_path.parent == self.storage.place_image_dir(self.current_place.id)

    def _is_saved_visit_image(self, image_path: Path) -> bool:
        if self.current_place is None:
            return False
        visit = self._current_visit()
        if visit is None:
            return False
        current_dir = self.storage.visit_image_dir(self.current_place.id, visit.id)
        if image_path.parent == current_dir:
            return True
        if visit.id.endswith("_legacy") and image_path.parent == self.storage.place_image_dir(self.current_place.id):
            return True
        return False

    def _update_place_image_preview(self) -> None:
        self._update_image_preview(self._current_place_image_path(), self.place_image_preview)

    def _update_visit_image_preview(self) -> None:
        self._update_image_preview(self._current_visit_image_path(), self.visit_image_preview)

    def _update_image_preview(self, image_path: Path | None, preview_label: QLabel) -> None:
        if image_path is None:
            preview_label.setPixmap(QPixmap())
            preview_label.setText("未选择图片")
            return
        if not image_path.exists():
            preview_label.setPixmap(QPixmap())
            preview_label.setText("图片文件不存在")
            return

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            preview_label.setPixmap(QPixmap())
            preview_label.setText("当前图片无法预览")
            return

        preview = pixmap.scaled(
            preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        preview_label.setText("")
        preview_label.setPixmap(preview)

    def _current_place_image_path(self) -> Path | None:
        row = self.place_image_list.currentRow()
        if row < 0 or row >= len(self.place_image_items):
            return None
        return self.place_image_items[row].source_path

    def _current_visit_image_path(self) -> Path | None:
        items = self._current_visit_image_items()
        row = self.visit_image_list.currentRow()
        if row < 0 or row >= len(items):
            return None
        return items[row].source_path

    def _open_image(self, image_path: Path | None) -> None:
        if image_path is None:
            return
        if not image_path.exists():
            QMessageBox.warning(self, "图片不存在", f"找不到图片文件：\n{image_path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(image_path)))

    def _mark_dirty(self, *_args) -> None:
        if self._is_loading_form or self._is_loading_place_image_details or self._is_loading_visit_image_details:
            return
        self._set_dirty(True)

    def _set_dirty(self, is_dirty: bool) -> None:
        if self.is_dirty == is_dirty:
            return
        self.is_dirty = is_dirty
        self.dirty_state_changed.emit(self.is_dirty)

    def _maybe_keep_changes(self) -> bool:
        if not self.is_dirty:
            return True

        reply = QMessageBox.question(
            self,
            "未保存更改",
            "当前地点足迹有未保存内容，是否先保存？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_place()
            return not self.is_dirty
        if reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _build_place_list_text(self, place: FootprintPlace) -> str:
        return f"{place.display_title}\n已关联 {len(place.visits)} 个日期"

    def _build_visit_list_text(self, visit: FootprintVisit) -> str:
        summary = visit.thought.strip().splitlines()[0] if visit.thought.strip() else "未填写当天感悟"
        summary = summary[:18]
        return f"{visit.display_title}\n{summary}"

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
