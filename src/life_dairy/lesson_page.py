from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, QSignalBlocker, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
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

from .autosave import AutoSaveMixin
from .book_page import DiaryPickerDialog
from .lesson_storage import LESSON_CATEGORIES, LESSON_SEVERITIES, LessonStorage
from .models import LessonEntry, LessonImageDraft, LessonRelatedDiary
from .storage import DiaryStorage
from .ui_helpers import make_scroll_area


class LessonPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)
    open_diary_requested = Signal(str, str)

    def __init__(
        self,
        storage: LessonStorage,
        diary_storage: DiaryStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.diary_storage = diary_storage
        self.current_lesson: LessonEntry | None = None
        self.image_items: list[LessonImageDraft] = []
        self.is_dirty = False
        self._is_loading_form = False
        self._is_loading_image_details = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_lesson_list()
        if self.lesson_list.count() > 0:
            self.lesson_list.setCurrentRow(0)
        else:
            self.new_lesson()

    def has_unsaved_changes(self) -> bool:
        return self.is_dirty

    def maybe_finish_pending_changes(self) -> bool:
        return AutoSaveMixin.maybe_finish_pending_changes(self)

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

        title = QLabel("教训与反思", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 类型 / 标签 / 正文")
        self.search_input.textChanged.connect(self.refresh_lesson_list)

        self.category_filter_combo = QComboBox(widget)
        self.category_filter_combo.addItems(["全部", *LESSON_CATEGORIES])
        self.category_filter_combo.currentTextChanged.connect(self.refresh_lesson_list)

        self.new_button = QPushButton("新建反思记录", widget)
        self.new_button.clicked.connect(self.new_lesson)

        self.delete_button = QPushButton("删除当前反思", widget)
        self.delete_button.clicked.connect(self.delete_current_lesson)

        self.lesson_list = QListWidget(widget)
        self.lesson_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.category_filter_combo)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.lesson_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_lesson)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_lesson)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addStretch(1)

        info_group = QGroupBox("反思信息", widget)
        info_layout = QVBoxLayout(info_group)

        form = QFormLayout()
        self.title_input = QLineEdit(info_group)
        self.title_input.setPlaceholderText("这次反思的标题")
        self.title_input.textChanged.connect(self._mark_dirty)

        self.date_edit = QDateEdit(info_group)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.dateChanged.connect(self._mark_dirty)

        self.category_combo = QComboBox(info_group)
        self.category_combo.addItems(LESSON_CATEGORIES)
        self.category_combo.currentTextChanged.connect(self._mark_dirty)

        self.severity_combo = QComboBox(info_group)
        self.severity_combo.addItems(LESSON_SEVERITIES)
        self.severity_combo.currentTextChanged.connect(self._mark_dirty)

        self.tags_input = QLineEdit(info_group)
        self.tags_input.setPlaceholderText("多个标签用逗号分隔")
        self.tags_input.textChanged.connect(self._mark_dirty)

        form.addRow("标题", self.title_input)
        form.addRow("日期", self.date_edit)
        form.addRow("事件类型", self.category_combo)
        form.addRow("严重程度", self.severity_combo)
        form.addRow("标签", self.tags_input)

        self.event_edit = self._make_text_edit("事件经过")
        self.judgment_edit = self._make_text_edit("当时我是怎么判断的")
        self.result_edit = self._make_text_edit("结果是什么")
        self.mistake_edit = self._make_text_edit("错误原因 / 判断偏差")
        self.root_cause_edit = self._make_text_edit("真正的问题是什么")
        self.cost_edit = self._make_text_edit("这次的代价")
        self.next_action_edit = self._make_text_edit("下次策略")
        self.one_sentence_input = QLineEdit(info_group)
        self.one_sentence_input.setPlaceholderText("把这次教训压缩成一句话")
        self.one_sentence_input.textChanged.connect(self._mark_dirty)

        info_layout.addLayout(form)
        info_layout.addWidget(QLabel("事件经过", info_group))
        info_layout.addWidget(self.event_edit)
        info_layout.addWidget(QLabel("当时判断", info_group))
        info_layout.addWidget(self.judgment_edit)
        info_layout.addWidget(QLabel("结果是什么", info_group))
        info_layout.addWidget(self.result_edit)
        info_layout.addWidget(QLabel("错误原因", info_group))
        info_layout.addWidget(self.mistake_edit)
        info_layout.addWidget(QLabel("真正的问题是什么", info_group))
        info_layout.addWidget(self.root_cause_edit)
        info_layout.addWidget(QLabel("这次的代价", info_group))
        info_layout.addWidget(self.cost_edit)
        info_layout.addWidget(QLabel("下次策略", info_group))
        info_layout.addWidget(self.next_action_edit)
        info_layout.addWidget(QLabel("一句话教训", info_group))
        info_layout.addWidget(self.one_sentence_input)

        lower_splitter = QSplitter(Qt.Orientation.Horizontal, widget)
        lower_splitter.setMinimumHeight(300)
        lower_splitter.addWidget(self._build_related_group())
        lower_splitter.addWidget(self._build_image_group())
        lower_splitter.setChildrenCollapsible(False)
        lower_splitter.setSizes([430, 520])

        right_splitter = QSplitter(Qt.Orientation.Vertical, widget)
        right_splitter.addWidget(info_group)
        right_splitter.addWidget(lower_splitter)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 0)
        right_splitter.setSizes([520, 320])

        layout.addLayout(action_row)
        layout.addWidget(right_splitter, 1)
        return widget

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit(self)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(95)
        edit.textChanged.connect(self._mark_dirty)
        return edit

    def _build_related_group(self) -> QWidget:
        group = QGroupBox("关联日记", self)
        layout = QVBoxLayout(group)

        action_row = QHBoxLayout()
        self.add_related_button = QPushButton("关联一篇日记", group)
        self.add_related_button.clicked.connect(self.add_related_diary)
        self.remove_related_button = QPushButton("移除关联", group)
        self.remove_related_button.clicked.connect(self.remove_selected_related_diary)
        self.open_related_button = QPushButton("打开日记", group)
        self.open_related_button.clicked.connect(self.open_selected_related_diary)
        action_row.addWidget(self.add_related_button)
        action_row.addWidget(self.remove_related_button)
        action_row.addWidget(self.open_related_button)

        self.related_list = QListWidget(group)
        self.related_list.currentItemChanged.connect(self._update_related_buttons)

        layout.addLayout(action_row)
        layout.addWidget(self.related_list, 1)
        return group

    def _build_image_group(self) -> QWidget:
        group = QGroupBox("图片 / 截图", self)
        layout = QHBoxLayout(group)

        left = QVBoxLayout()
        self.image_list = QListWidget(group)
        self.image_list.currentItemChanged.connect(self._on_image_selection_changed)

        button_row = QHBoxLayout()
        self.add_image_button = QPushButton("添加图片", group)
        self.add_image_button.clicked.connect(self.add_images)
        self.open_image_button = QPushButton("打开图片", group)
        self.open_image_button.clicked.connect(self.open_selected_image)
        self.remove_image_button = QPushButton("移除图片", group)
        self.remove_image_button.clicked.connect(self.remove_selected_image)
        button_row.addWidget(self.add_image_button)
        button_row.addWidget(self.open_image_button)
        button_row.addWidget(self.remove_image_button)

        self.image_label_input = QLineEdit(group)
        self.image_label_input.setPlaceholderText("图片备注名")
        self.image_label_input.textChanged.connect(self._update_selected_image_label)

        left.addWidget(self.image_list, 1)
        left.addLayout(button_row)
        left.addWidget(self.image_label_input)

        self.image_preview = QLabel("未选择图片", group)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(220, 180)
        self.image_preview.setStyleSheet("border: 1px solid #cccccc; background: #fafafa; color: #666666;")

        layout.addLayout(left, 2)
        layout.addWidget(self.image_preview, 1)
        return group

    def refresh_lesson_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id
        if current_id is None and self.current_lesson is not None:
            current_id = self.current_lesson.id

        query = self.search_input.text() if hasattr(self, "search_input") else ""
        category = self.category_filter_combo.currentText() if hasattr(self, "category_filter_combo") else "全部"
        blocker = QSignalBlocker(self.lesson_list)
        self.lesson_list.clear()

        target_row = -1
        for row, lesson in enumerate(self.storage.list_lessons(query, category)):
            item = QListWidgetItem(self._build_lesson_list_text(lesson))
            item.setData(Qt.ItemDataRole.UserRole, lesson.id)
            item.setToolTip(lesson.one_sentence or lesson.event[:150] or lesson.display_title)
            self.lesson_list.addItem(item)
            if current_id and lesson.id == current_id:
                target_row = row

        if target_row >= 0:
            self.lesson_list.setCurrentRow(target_row)
        del blocker

    def new_lesson(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_lesson())
        self.lesson_list.blockSignals(True)
        self.lesson_list.clearSelection()
        self.lesson_list.blockSignals(False)
        self._show_status("已创建新的反思草稿。", 3000)

    def save_lesson(self) -> bool:
        lesson = self._read_form()
        try:
            saved = self.storage.save_lesson(lesson, self.image_items)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存反思记录时出错：\n{exc}")
            return False

        self._fill_form(saved)
        self.refresh_lesson_list(select_id=saved.id)
        self._show_status("已保存反思记录到本地。", 3000)
        return True

    def reload_current_lesson(self) -> None:
        if self.current_lesson is None:
            return
        self._suspend_auto_save()
        if self.is_dirty:
            reply = QMessageBox.question(
                self,
                "恢复确认",
                "当前有未保存修改，恢复后会丢失这些改动。是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self._resume_auto_save()
                return
        if self.current_lesson.id and self.storage.lesson_dir(self.current_lesson.id).exists():
            try:
                lesson = self.storage.load_lesson(self.current_lesson.id)
            except Exception as exc:
                QMessageBox.critical(self, "读取失败", f"恢复已保存内容时出错：\n{exc}")
                self._resume_auto_save()
                return
            self._fill_form(lesson)
            self.refresh_lesson_list(select_id=lesson.id)
            self._show_status("已恢复到上次保存的反思内容。", 3000)
        self._resume_auto_save()

    def delete_current_lesson(self) -> None:
        if self.current_lesson is None:
            return

        if not self.storage.lesson_dir(self.current_lesson.id).exists():
            reply = QMessageBox.question(
                self,
                "放弃草稿",
                "这条反思草稿还没有保存，确定要放弃吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._discard_current_draft("已放弃未保存的反思草稿。")
            return

        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定要删除这条反思记录吗？\n\n{self.current_lesson.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        lesson_id = self.current_lesson.id
        try:
            self.storage.delete_lesson(lesson_id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除反思记录时出错：\n{exc}")
            return

        self.current_lesson = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_lesson_list()
        if self.lesson_list.count() > 0:
            self.lesson_list.setCurrentRow(0)
        else:
            self.new_lesson()
        self._show_status("已删除当前反思记录。", 3000)

    def add_related_diary(self) -> None:
        dialog = DiaryPickerDialog(self.diary_storage, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dialog.selected_relation()
        if selected is None:
            return
        relation = LessonRelatedDiary(
            entry_id=selected.entry_id,
            date=selected.date,
            title=selected.title,
        )

        if self.current_lesson is None:
            self.current_lesson = self.storage.create_empty_lesson()

        existing_ids = {item.entry_id for item in self.current_lesson.related_diaries}
        if relation.entry_id in existing_ids:
            QMessageBox.information(self, "已关联过", "这篇日记已经关联过了。")
            return

        self.current_lesson.related_diaries.append(relation)
        self._refresh_related_list(select_entry_id=relation.entry_id)
        self._mark_dirty()
        self._show_status("已关联一篇日记，保存后生效。", 3000)

    def remove_selected_related_diary(self) -> None:
        relation = self._current_related_diary()
        if relation is None or self.current_lesson is None:
            return

        remaining = [item for item in self.current_lesson.related_diaries if item.entry_id != relation.entry_id]
        self.current_lesson.related_diaries = remaining
        next_entry_id = remaining[min(self.related_list.currentRow(), len(remaining) - 1)].entry_id if remaining else None
        self._refresh_related_list(select_entry_id=next_entry_id)
        self._mark_dirty()
        self._show_status("已移除所选日记关联，保存后生效。", 3000)

    def open_selected_related_diary(self) -> None:
        relation = self._current_related_diary()
        if relation is None:
            return
        self.open_diary_requested.emit(relation.entry_id, relation.date)

    def add_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not files:
            return

        existing: set[str] = set()
        for image_item in self.image_items:
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
            self.image_items.append(LessonImageDraft(source_path=path, label=""))
            existing.add(normalized)
            added_count += 1

        if added_count == 0:
            return

        self._refresh_image_list(select_row=len(self.image_items) - 1)
        self._mark_dirty()
        self._show_status(f"已加入 {added_count} 张图片，保存后生效。", 3000)

    def remove_selected_image(self) -> None:
        current_row = self.image_list.currentRow()
        if current_row < 0:
            return
        del self.image_items[current_row]
        next_row = min(current_row, len(self.image_items) - 1)
        self._refresh_image_list(select_row=next_row if next_row >= 0 else None)
        self._mark_dirty()
        self._show_status("已移除所选图片，保存后生效。", 3000)

    def open_selected_image(self) -> None:
        image_path = self._current_image_path()
        if image_path is None:
            return
        if not image_path.exists():
            QMessageBox.warning(self, "图片不存在", f"找不到图片文件：\n{image_path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(image_path)))

    def _fill_form(self, lesson: LessonEntry) -> None:
        self._is_loading_form = True
        self.current_lesson = lesson
        self.image_items = [
            LessonImageDraft(
                source_path=self.storage.resolve_image_path(lesson.id, image.file_name),
                label=image.label,
            )
            for image in lesson.images
        ]
        date_value = QDate.fromString(lesson.date, "yyyy-MM-dd")
        if not date_value.isValid():
            date_value = QDate.currentDate()

        try:
            self.title_input.setText(lesson.title)
            self.date_edit.setDate(date_value)
            self._set_combo_text(self.category_combo, lesson.category)
            self._set_combo_text(self.severity_combo, lesson.severity)
            self.tags_input.setText(", ".join(lesson.tags))
            self.event_edit.setPlainText(lesson.event)
            self.judgment_edit.setPlainText(lesson.judgment)
            self.result_edit.setPlainText(lesson.result)
            self.mistake_edit.setPlainText(lesson.mistake)
            self.root_cause_edit.setPlainText(lesson.root_cause)
            self.cost_edit.setPlainText(lesson.cost)
            self.next_action_edit.setPlainText(lesson.next_action)
            self.one_sentence_input.setText(lesson.one_sentence)
            self._refresh_related_list()
            self._refresh_image_list()
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> LessonEntry:
        if self.current_lesson is None:
            self.current_lesson = self.storage.create_empty_lesson()

        tags = [
            item.strip()
            for item in self.tags_input.text().replace("，", ",").split(",")
            if item.strip()
        ]
        self.current_lesson.title = self.title_input.text().strip()
        self.current_lesson.date = self.date_edit.date().toString("yyyy-MM-dd")
        self.current_lesson.category = self.category_combo.currentText().strip() or "其他"
        self.current_lesson.severity = self.severity_combo.currentText().strip() or "中等"
        self.current_lesson.tags = tags
        self.current_lesson.event = self.event_edit.toPlainText()
        self.current_lesson.judgment = self.judgment_edit.toPlainText()
        self.current_lesson.result = self.result_edit.toPlainText()
        self.current_lesson.mistake = self.mistake_edit.toPlainText()
        self.current_lesson.root_cause = self.root_cause_edit.toPlainText()
        self.current_lesson.cost = self.cost_edit.toPlainText()
        self.current_lesson.next_action = self.next_action_edit.toPlainText()
        self.current_lesson.one_sentence = self.one_sentence_input.text().strip()
        return self.current_lesson

    def _open_lesson_by_id(self, lesson_id: str, status_message: str | None = None) -> None:
        try:
            lesson = self.storage.load_lesson(lesson_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取反思记录时出错：\n{exc}")
            return
        self._fill_form(lesson)
        self.refresh_lesson_list(select_id=lesson.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_lesson = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_lesson_list()
        if self.lesson_list.count() > 0:
            self.lesson_list.setCurrentRow(0)
        else:
            self.new_lesson()
        self._show_status(status_message, 3000)

    def _on_current_item_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.lesson_list)
            self.lesson_list.setCurrentItem(previous)
            del blocker
            return
        lesson_id = current.data(Qt.ItemDataRole.UserRole)
        if self.current_lesson is not None and self.current_lesson.id == lesson_id:
            return
        self._open_lesson_by_id(lesson_id, status_message="已重新打开这条反思记录。")

    def _refresh_related_list(self, select_entry_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.related_list)
        self.related_list.clear()
        target_row = -1
        for row, relation in enumerate(self.current_lesson.related_diaries if self.current_lesson is not None else []):
            item = QListWidgetItem(relation.display_title)
            item.setData(Qt.ItemDataRole.UserRole, relation.entry_id)
            self.related_list.addItem(item)
            if select_entry_id and relation.entry_id == select_entry_id:
                target_row = row
        if target_row >= 0:
            self.related_list.setCurrentRow(target_row)
        elif self.related_list.count() > 0:
            self.related_list.setCurrentRow(0)
        del blocker
        self._update_related_buttons()

    def _current_related_diary(self) -> LessonRelatedDiary | None:
        if self.current_lesson is None:
            return None
        current_item = self.related_list.currentItem()
        entry_id = current_item.data(Qt.ItemDataRole.UserRole) if current_item else None
        if not entry_id:
            return None
        for relation in self.current_lesson.related_diaries:
            if relation.entry_id == entry_id:
                return relation
        return None

    def _update_related_buttons(self, *_args) -> None:
        enabled = self._current_related_diary() is not None
        self.remove_related_button.setEnabled(enabled)
        self.open_related_button.setEnabled(enabled)

    def _on_image_selection_changed(self, *_args) -> None:
        self._update_image_preview()
        row = self.image_list.currentRow()
        self._is_loading_image_details = True
        try:
            if row < 0 or row >= len(self.image_items):
                self.image_label_input.clear()
                return
            self.image_label_input.setText(self.image_items[row].label)
        finally:
            self._is_loading_image_details = False

    def _update_selected_image_label(self, text: str) -> None:
        if self._is_loading_image_details:
            return
        row = self.image_list.currentRow()
        if row < 0 or row >= len(self.image_items):
            return
        normalized = text.strip()
        if self.image_items[row].label == normalized:
            return
        self.image_items[row].label = normalized
        self._refresh_image_list(select_row=row)
        self._mark_dirty()

    def _refresh_image_list(self, select_row: int | None = 0) -> None:
        blocker = QSignalBlocker(self.image_list)
        self.image_list.clear()
        for index, image_item in enumerate(self.image_items, start=1):
            label = image_item.label.strip() or f"图片 {index}"
            if not self._is_current_lesson_image(image_item.source_path):
                label = f"{label} (待保存)"
            item = QListWidgetItem(label)
            item.setToolTip(str(image_item.source_path))
            self.image_list.addItem(item)
        if select_row is not None and 0 <= select_row < self.image_list.count():
            self.image_list.setCurrentRow(select_row)
        del blocker
        self._on_image_selection_changed()

    def _update_image_preview(self) -> None:
        image_path = self._current_image_path()
        if image_path is None:
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("未选择图片")
            return
        if not image_path.exists():
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("图片文件不存在")
            return
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("当前图片无法预览")
            return
        preview = pixmap.scaled(
            self.image_preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_preview.setText("")
        self.image_preview.setPixmap(preview)

    def _current_image_path(self) -> Path | None:
        row = self.image_list.currentRow()
        if row < 0 or row >= len(self.image_items):
            return None
        return self.image_items[row].source_path

    def _is_current_lesson_image(self, image_path: Path) -> bool:
        if self.current_lesson is None:
            return False
        return image_path.parent == self.storage.image_dir(self.current_lesson.id)

    def _set_combo_text(self, combo: QComboBox, text: str) -> None:
        index = combo.findText(text)
        if index < 0:
            index = 0
        combo.setCurrentIndex(index)

    def _build_lesson_list_text(self, lesson: LessonEntry) -> str:
        subtitle_parts = [lesson.date, lesson.category, lesson.severity]
        if lesson.one_sentence:
            subtitle_parts.append(lesson.one_sentence)
        return f"{lesson.display_title}\n{' | '.join(subtitle_parts)}"

    def _mark_dirty(self, *_args) -> None:
        if self._is_loading_form or self._is_loading_image_details:
            return
        self._set_dirty(True)

    def _set_dirty(self, is_dirty: bool) -> None:
        if self.is_dirty == is_dirty:
            if is_dirty:
                self._on_dirty_state_changed_for_autosave(True)
            return
        self.is_dirty = is_dirty
        self.dirty_state_changed.emit(self.is_dirty)
        self._on_dirty_state_changed_for_autosave(self.is_dirty)

    def _maybe_keep_changes(self) -> bool:
        return self.maybe_finish_pending_changes()

    def _auto_save_now(self) -> bool:
        return self.save_lesson()

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_lesson is None:
            return False
        if self.storage.lesson_dir(self.current_lesson.id).exists():
            return True
        return bool(
            self.title_input.text().strip()
            or self.tags_input.text().strip()
            or self.event_edit.toPlainText().strip()
            or self.judgment_edit.toPlainText().strip()
            or self.result_edit.toPlainText().strip()
            or self.mistake_edit.toPlainText().strip()
            or self.root_cause_edit.toPlainText().strip()
            or self.cost_edit.toPlainText().strip()
            or self.next_action_edit.toPlainText().strip()
            or self.one_sentence_input.text().strip()
            or self.image_items
            or self.current_lesson.related_diaries
        )

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
