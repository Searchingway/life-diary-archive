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
from .lesson_storage import LessonStorage
from .models import (
    SelfAnalysisEntry,
    SelfAnalysisImageDraft,
    SelfAnalysisRelatedDiary,
    SelfAnalysisRelatedLesson,
)
from .self_analysis_storage import SELF_ANALYSIS_TYPES, SelfAnalysisStorage
from .storage import DiaryStorage
from .ui_helpers import make_scroll_area


class LessonPickerDialog(QDialog):
    def __init__(self, lesson_storage: LessonStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("选择关联教训")
        self.resize(560, 420)
        self.lesson_storage = lesson_storage
        self._selected: SelfAnalysisRelatedLesson | None = None

        layout = QVBoxLayout(self)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜索教训标题 / 类型 / 标签 / 正文")
        self.lesson_list = QListWidget(self)
        self.search_input.textChanged.connect(self._refresh)
        self.lesson_list.itemDoubleClicked.connect(self._accept_current)

        button_row = QHBoxLayout()
        ok_button = QPushButton("关联所选教训", self)
        cancel_button = QPushButton("取消", self)
        ok_button.clicked.connect(self._accept_current)
        cancel_button.clicked.connect(self.reject)
        button_row.addStretch(1)
        button_row.addWidget(ok_button)
        button_row.addWidget(cancel_button)

        layout.addWidget(self.search_input)
        layout.addWidget(self.lesson_list, 1)
        layout.addLayout(button_row)
        self._refresh()

    def selected_relation(self) -> SelfAnalysisRelatedLesson | None:
        return self._selected

    def _refresh(self) -> None:
        current_id = self.current_lesson_id()
        self.lesson_list.clear()
        target_row = -1
        for row, lesson in enumerate(self.lesson_storage.list_lessons(self.search_input.text())):
            item = QListWidgetItem(f"{lesson.date} | {lesson.display_title}\n{lesson.category}")
            item.setData(Qt.ItemDataRole.UserRole, lesson.id)
            item.setToolTip(lesson.one_sentence or lesson.event[:150] or lesson.display_title)
            self.lesson_list.addItem(item)
            if current_id and lesson.id == current_id:
                target_row = row
        if target_row >= 0:
            self.lesson_list.setCurrentRow(target_row)
        elif self.lesson_list.count() > 0:
            self.lesson_list.setCurrentRow(0)

    def current_lesson_id(self) -> str:
        item = self.lesson_list.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole)) if item else ""

    def _accept_current(self) -> None:
        lesson_id = self.current_lesson_id()
        if not lesson_id:
            return
        lesson = self.lesson_storage.load_lesson(lesson_id)
        self._selected = SelfAnalysisRelatedLesson(
            lesson_id=lesson.id,
            date=lesson.date,
            title=lesson.display_title,
        )
        self.accept()


class SelfAnalysisPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)
    open_diary_requested = Signal(str, str)
    open_lesson_requested = Signal(str)

    def __init__(
        self,
        storage: SelfAnalysisStorage,
        diary_storage: DiaryStorage,
        lesson_storage: LessonStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.diary_storage = diary_storage
        self.lesson_storage = lesson_storage
        self.current_analysis: SelfAnalysisEntry | None = None
        self.image_items: list[SelfAnalysisImageDraft] = []
        self.is_dirty = False
        self._is_loading_form = False
        self._is_loading_image_details = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_analysis_list()
        if self.analysis_list.count() > 0:
            self.analysis_list.setCurrentRow(0)
        else:
            self.new_analysis()

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
        splitter.setSizes([300, 920])
        layout.addWidget(make_scroll_area(splitter))

    def _build_sidebar(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("自我分析", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 类型 / 标签 / 正文")
        self.search_input.textChanged.connect(self.refresh_analysis_list)
        self.type_filter_combo = QComboBox(widget)
        self.type_filter_combo.addItems(["全部", *SELF_ANALYSIS_TYPES])
        self.type_filter_combo.currentTextChanged.connect(self.refresh_analysis_list)
        self.new_button = QPushButton("新建自我分析", widget)
        self.new_button.clicked.connect(self.new_analysis)
        self.delete_button = QPushButton("删除当前记录", widget)
        self.delete_button.clicked.connect(self.delete_current_analysis)
        self.analysis_list = QListWidget(widget)
        self.analysis_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.type_filter_combo)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.analysis_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_analysis)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_analysis)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addStretch(1)

        info_group = QGroupBox("自我分析信息", widget)
        info_layout = QVBoxLayout(info_group)
        form = QFormLayout()
        self.title_input = QLineEdit(info_group)
        self.title_input.setPlaceholderText("这次自我观察的标题")
        self.title_input.textChanged.connect(self._mark_dirty)
        self.date_edit = QDateEdit(info_group)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.dateChanged.connect(self._mark_dirty)
        self.type_combo = QComboBox(info_group)
        self.type_combo.addItems(SELF_ANALYSIS_TYPES)
        self.type_combo.currentTextChanged.connect(self._mark_dirty)
        self.tags_input = QLineEdit(info_group)
        self.tags_input.setPlaceholderText("多个标签用逗号分隔")
        self.tags_input.textChanged.connect(self._mark_dirty)
        form.addRow("标题", self.title_input)
        form.addRow("日期", self.date_edit)
        form.addRow("分析类型", self.type_combo)
        form.addRow("标签", self.tags_input)
        info_layout.addLayout(form)

        self.section_edits: dict[str, QTextEdit] = {}
        for attr, label in [
            ("trigger_event", "触发事件"),
            ("emotion", "当时的情绪"),
            ("body_reaction", "当时的身体反应"),
            ("surface_want", "我表面上想要什么"),
            ("real_fear", "我真正害怕什么"),
            ("real_want", "我真正想要什么"),
            ("repeated_pattern", "我在重复什么模式"),
            ("imagined_judgment", "我想象中的别人怎么看我"),
            ("defense", "我采取了什么防御方式"),
            ("similar_experience", "这件事和过去哪些经历相似"),
            ("insight", "我从中看见了什么"),
            ("next_action", "下一步我可以怎么做"),
        ]:
            edit = self._make_text_edit(label)
            self.section_edits[attr] = edit
            info_layout.addWidget(QLabel(label, info_group))
            info_layout.addWidget(edit)

        lower_splitter = QSplitter(Qt.Orientation.Horizontal, widget)
        lower_splitter.setMinimumHeight(320)
        lower_splitter.addWidget(self._build_related_group())
        lower_splitter.addWidget(self._build_image_group())
        lower_splitter.setChildrenCollapsible(False)
        lower_splitter.setSizes([450, 520])

        right_splitter = QSplitter(Qt.Orientation.Vertical, widget)
        right_splitter.addWidget(info_group)
        right_splitter.addWidget(lower_splitter)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 0)
        right_splitter.setSizes([620, 320])

        layout.addLayout(action_row)
        layout.addWidget(right_splitter, 1)
        return widget

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit(self)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(88)
        edit.textChanged.connect(self._mark_dirty)
        return edit

    def _build_related_group(self) -> QWidget:
        group = QGroupBox("关联记录", self)
        layout = QHBoxLayout(group)
        diary_box = QVBoxLayout()
        lesson_box = QVBoxLayout()

        diary_buttons = QHBoxLayout()
        self.add_related_diary_button = QPushButton("关联日记", group)
        self.add_related_diary_button.clicked.connect(self.add_related_diary)
        self.remove_related_diary_button = QPushButton("移除", group)
        self.remove_related_diary_button.clicked.connect(self.remove_selected_related_diary)
        self.open_related_diary_button = QPushButton("打开日记", group)
        self.open_related_diary_button.clicked.connect(self.open_selected_related_diary)
        diary_buttons.addWidget(self.add_related_diary_button)
        diary_buttons.addWidget(self.remove_related_diary_button)
        diary_buttons.addWidget(self.open_related_diary_button)
        self.related_diary_list = QListWidget(group)
        self.related_diary_list.currentItemChanged.connect(self._update_related_buttons)
        diary_box.addWidget(QLabel("关联日记", group))
        diary_box.addLayout(diary_buttons)
        diary_box.addWidget(self.related_diary_list, 1)

        lesson_buttons = QHBoxLayout()
        self.add_related_lesson_button = QPushButton("关联教训", group)
        self.add_related_lesson_button.clicked.connect(self.add_related_lesson)
        self.remove_related_lesson_button = QPushButton("移除", group)
        self.remove_related_lesson_button.clicked.connect(self.remove_selected_related_lesson)
        self.open_related_lesson_button = QPushButton("打开教训", group)
        self.open_related_lesson_button.clicked.connect(self.open_selected_related_lesson)
        lesson_buttons.addWidget(self.add_related_lesson_button)
        lesson_buttons.addWidget(self.remove_related_lesson_button)
        lesson_buttons.addWidget(self.open_related_lesson_button)
        self.related_lesson_list = QListWidget(group)
        self.related_lesson_list.currentItemChanged.connect(self._update_related_buttons)
        lesson_box.addWidget(QLabel("关联教训与反思", group))
        lesson_box.addLayout(lesson_buttons)
        lesson_box.addWidget(self.related_lesson_list, 1)

        layout.addLayout(diary_box, 1)
        layout.addLayout(lesson_box, 1)
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

    def refresh_analysis_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id or (self.current_analysis.id if self.current_analysis is not None else None)
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        analysis_type = self.type_filter_combo.currentText() if hasattr(self, "type_filter_combo") else "全部"
        blocker = QSignalBlocker(self.analysis_list)
        self.analysis_list.clear()
        target_row = -1
        for row, analysis in enumerate(self.storage.list_analyses(query, analysis_type)):
            item = QListWidgetItem(self._build_analysis_list_text(analysis))
            item.setData(Qt.ItemDataRole.UserRole, analysis.id)
            item.setToolTip(analysis.insight or analysis.trigger_event[:150] or analysis.display_title)
            self.analysis_list.addItem(item)
            if current_id and analysis.id == current_id:
                target_row = row
        if target_row >= 0:
            self.analysis_list.setCurrentRow(target_row)
        del blocker

    def new_analysis(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_analysis())
        self.analysis_list.blockSignals(True)
        self.analysis_list.clearSelection()
        self.analysis_list.blockSignals(False)
        self._show_status("已创建新的自我分析草稿。", 3000)

    def save_analysis(self) -> bool:
        analysis = self._read_form()
        try:
            saved = self.storage.save_analysis(analysis, self.image_items)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存自我分析记录时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_analysis_list(select_id=saved.id)
        self._show_status("已保存自我分析记录到本地。", 3000)
        return True

    def reload_current_analysis(self) -> None:
        if self.current_analysis is None:
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
        if self.current_analysis.id and self.storage.analysis_dir(self.current_analysis.id).exists():
            try:
                analysis = self.storage.load_analysis(self.current_analysis.id)
            except Exception as exc:
                QMessageBox.critical(self, "读取失败", f"恢复已保存内容时出错：\n{exc}")
                self._resume_auto_save()
                return
            self._fill_form(analysis)
            self.refresh_analysis_list(select_id=analysis.id)
            self._show_status("已恢复到上次保存的自我分析内容。", 3000)
        self._resume_auto_save()

    def delete_current_analysis(self) -> None:
        if self.current_analysis is None:
            return
        if not self.storage.analysis_dir(self.current_analysis.id).exists():
            reply = QMessageBox.question(
                self,
                "放弃草稿",
                "这条自我分析草稿还没有保存，确定要放弃吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._discard_current_draft("已放弃未保存的自我分析草稿。")
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定要删除这条自我分析记录吗？\n\n{self.current_analysis.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_analysis(self.current_analysis.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除自我分析记录时出错：\n{exc}")
            return
        self.current_analysis = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_analysis_list()
        if self.analysis_list.count() > 0:
            self.analysis_list.setCurrentRow(0)
        else:
            self.new_analysis()
        self._show_status("已删除当前自我分析记录。", 3000)

    def add_related_diary(self) -> None:
        dialog = DiaryPickerDialog(self.diary_storage, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected = dialog.selected_relation()
        if selected is None:
            return
        if self.current_analysis is None:
            self.current_analysis = self.storage.create_empty_analysis()
        if selected.entry_id in {item.entry_id for item in self.current_analysis.related_diaries}:
            QMessageBox.information(self, "已关联过", "这篇日记已经关联过了。")
            return
        relation = SelfAnalysisRelatedDiary(selected.entry_id, selected.date, selected.title)
        self.current_analysis.related_diaries.append(relation)
        self._refresh_related_diary_list(select_entry_id=relation.entry_id)
        self._mark_dirty()

    def add_related_lesson(self) -> None:
        dialog = LessonPickerDialog(self.lesson_storage, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        relation = dialog.selected_relation()
        if relation is None:
            return
        if self.current_analysis is None:
            self.current_analysis = self.storage.create_empty_analysis()
        if relation.lesson_id in {item.lesson_id for item in self.current_analysis.related_lessons}:
            QMessageBox.information(self, "已关联过", "这条教训记录已经关联过了。")
            return
        self.current_analysis.related_lessons.append(relation)
        self._refresh_related_lesson_list(select_lesson_id=relation.lesson_id)
        self._mark_dirty()

    def remove_selected_related_diary(self) -> None:
        relation = self._current_related_diary()
        if relation is None or self.current_analysis is None:
            return
        remaining = [item for item in self.current_analysis.related_diaries if item.entry_id != relation.entry_id]
        self.current_analysis.related_diaries = remaining
        next_id = remaining[min(self.related_diary_list.currentRow(), len(remaining) - 1)].entry_id if remaining else None
        self._refresh_related_diary_list(select_entry_id=next_id)
        self._mark_dirty()

    def remove_selected_related_lesson(self) -> None:
        relation = self._current_related_lesson()
        if relation is None or self.current_analysis is None:
            return
        remaining = [item for item in self.current_analysis.related_lessons if item.lesson_id != relation.lesson_id]
        self.current_analysis.related_lessons = remaining
        next_id = remaining[min(self.related_lesson_list.currentRow(), len(remaining) - 1)].lesson_id if remaining else None
        self._refresh_related_lesson_list(select_lesson_id=next_id)
        self._mark_dirty()

    def open_selected_related_diary(self) -> None:
        relation = self._current_related_diary()
        if relation is not None:
            self.open_diary_requested.emit(relation.entry_id, relation.date)

    def open_selected_related_lesson(self) -> None:
        relation = self._current_related_lesson()
        if relation is not None:
            self.open_lesson_requested.emit(relation.lesson_id)

    def add_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not files:
            return
        existing = {str(item.source_path.resolve()).lower() for item in self.image_items if item.source_path.exists()}
        added_count = 0
        for file_path in files:
            path = Path(file_path)
            if not path.exists():
                continue
            normalized = str(path.resolve()).lower()
            if normalized in existing:
                continue
            self.image_items.append(SelfAnalysisImageDraft(source_path=path, label=""))
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

    def open_selected_image(self) -> None:
        image_path = self._current_image_path()
        if image_path is None:
            return
        if not image_path.exists():
            QMessageBox.warning(self, "图片不存在", f"找不到图片文件：\n{image_path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(image_path)))

    def _fill_form(self, analysis: SelfAnalysisEntry) -> None:
        self._is_loading_form = True
        self.current_analysis = analysis
        self.image_items = [
            SelfAnalysisImageDraft(
                source_path=self.storage.resolve_image_path(analysis.id, image.file_name),
                label=image.label,
            )
            for image in analysis.images
        ]
        date_value = QDate.fromString(analysis.date, "yyyy-MM-dd")
        if not date_value.isValid():
            date_value = QDate.currentDate()
        try:
            self.title_input.setText(analysis.title)
            self.date_edit.setDate(date_value)
            self._set_combo_text(self.type_combo, analysis.analysis_type)
            self.tags_input.setText(", ".join(analysis.tags))
            for attr, edit in self.section_edits.items():
                edit.setPlainText(str(getattr(analysis, attr)))
            self._refresh_related_diary_list()
            self._refresh_related_lesson_list()
            self._refresh_image_list()
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> SelfAnalysisEntry:
        if self.current_analysis is None:
            self.current_analysis = self.storage.create_empty_analysis()
        tags = [item.strip() for item in self.tags_input.text().replace("，", ",").split(",") if item.strip()]
        self.current_analysis.title = self.title_input.text().strip()
        self.current_analysis.date = self.date_edit.date().toString("yyyy-MM-dd")
        self.current_analysis.analysis_type = self.type_combo.currentText().strip() or "其他"
        self.current_analysis.tags = tags
        for attr, edit in self.section_edits.items():
            setattr(self.current_analysis, attr, edit.toPlainText())
        return self.current_analysis

    def open_analysis_by_id(self, analysis_id: str, status_message: str | None = None) -> None:
        try:
            analysis = self.storage.load_analysis(analysis_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取自我分析记录时出错：\n{exc}")
            return
        self._fill_form(analysis)
        self.refresh_analysis_list(select_id=analysis.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_analysis = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_analysis_list()
        if self.analysis_list.count() > 0:
            self.analysis_list.setCurrentRow(0)
        else:
            self.new_analysis()
        self._show_status(status_message, 3000)

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.analysis_list)
            self.analysis_list.setCurrentItem(previous)
            del blocker
            return
        analysis_id = current.data(Qt.ItemDataRole.UserRole)
        if self.current_analysis is not None and self.current_analysis.id == analysis_id:
            return
        self.open_analysis_by_id(analysis_id, status_message="已重新打开这条自我分析记录。")

    def _refresh_related_diary_list(self, select_entry_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.related_diary_list)
        self.related_diary_list.clear()
        target_row = -1
        for row, relation in enumerate(self.current_analysis.related_diaries if self.current_analysis else []):
            item = QListWidgetItem(relation.display_title)
            item.setData(Qt.ItemDataRole.UserRole, relation.entry_id)
            self.related_diary_list.addItem(item)
            if select_entry_id and relation.entry_id == select_entry_id:
                target_row = row
        if target_row >= 0:
            self.related_diary_list.setCurrentRow(target_row)
        elif self.related_diary_list.count() > 0:
            self.related_diary_list.setCurrentRow(0)
        del blocker
        self._update_related_buttons()

    def _refresh_related_lesson_list(self, select_lesson_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.related_lesson_list)
        self.related_lesson_list.clear()
        target_row = -1
        for row, relation in enumerate(self.current_analysis.related_lessons if self.current_analysis else []):
            item = QListWidgetItem(relation.display_title)
            item.setData(Qt.ItemDataRole.UserRole, relation.lesson_id)
            self.related_lesson_list.addItem(item)
            if select_lesson_id and relation.lesson_id == select_lesson_id:
                target_row = row
        if target_row >= 0:
            self.related_lesson_list.setCurrentRow(target_row)
        elif self.related_lesson_list.count() > 0:
            self.related_lesson_list.setCurrentRow(0)
        del blocker
        self._update_related_buttons()

    def _current_related_diary(self) -> SelfAnalysisRelatedDiary | None:
        if self.current_analysis is None:
            return None
        item = self.related_diary_list.currentItem()
        entry_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next((relation for relation in self.current_analysis.related_diaries if relation.entry_id == entry_id), None)

    def _current_related_lesson(self) -> SelfAnalysisRelatedLesson | None:
        if self.current_analysis is None:
            return None
        item = self.related_lesson_list.currentItem()
        lesson_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next((relation for relation in self.current_analysis.related_lessons if relation.lesson_id == lesson_id), None)

    def _update_related_buttons(self, *_args) -> None:
        has_diary = self._current_related_diary() is not None
        has_lesson = self._current_related_lesson() is not None
        self.remove_related_diary_button.setEnabled(has_diary)
        self.open_related_diary_button.setEnabled(has_diary)
        self.remove_related_lesson_button.setEnabled(has_lesson)
        self.open_related_lesson_button.setEnabled(has_lesson)

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
            if not self._is_current_analysis_image(image_item.source_path):
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
        self.image_preview.setText("")
        self.image_preview.setPixmap(
            pixmap.scaled(
                self.image_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _current_image_path(self) -> Path | None:
        row = self.image_list.currentRow()
        if row < 0 or row >= len(self.image_items):
            return None
        return self.image_items[row].source_path

    def _is_current_analysis_image(self, image_path: Path) -> bool:
        if self.current_analysis is None:
            return False
        return image_path.parent == self.storage.image_dir(self.current_analysis.id)

    def _set_combo_text(self, combo: QComboBox, text: str) -> None:
        index = combo.findText(text)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _build_analysis_list_text(self, analysis: SelfAnalysisEntry) -> str:
        subtitle_parts = [analysis.date, analysis.analysis_type]
        if analysis.insight:
            subtitle_parts.append(analysis.insight)
        return f"{analysis.display_title}\n{' | '.join(subtitle_parts)}"

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
        analysis = self._read_form()
        try:
            self.storage.save_analysis(analysis, self.image_items)
        except Exception:
            return False
        self._set_dirty(False)
        return True

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_analysis is None:
            return False
        if self.storage.analysis_dir(self.current_analysis.id).exists():
            return True
        return bool(
            self.title_input.text().strip()
            or self.tags_input.text().strip()
            or any(edit.toPlainText().strip() for edit in self.section_edits.values())
            or self.image_items
            or self.current_analysis.related_diaries
            or self.current_analysis.related_lessons
        )

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
