from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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
from .plan_storage import PlanStorage
from .thought_storage import THOUGHT_STATUSES, THOUGHT_TYPES, ThoughtEntry, ThoughtStorage
from .ui_helpers import make_scroll_area


class ThoughtPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)
    plan_created = Signal(str)

    def __init__(self, storage: ThoughtStorage, plan_storage: PlanStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.storage = storage
        self.plan_storage = plan_storage
        self.current_thought: ThoughtEntry | None = None
        self.is_dirty = False
        self._is_loading_form = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_thought_list()
        if self.thought_list.count() > 0 and self.thought_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.thought_list.setCurrentRow(0)
        else:
            self.new_thought()

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

        title = QLabel("轻思考", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 描述 / 想法 / 结论 / 备注")
        self.search_input.textChanged.connect(self.refresh_thought_list)
        self.type_filter_combo = QComboBox(widget)
        self.type_filter_combo.addItems(["全部", *THOUGHT_TYPES])
        self.type_filter_combo.currentTextChanged.connect(self.refresh_thought_list)
        self.status_filter_combo = QComboBox(widget)
        self.status_filter_combo.addItems(["全部", *THOUGHT_STATUSES])
        self.status_filter_combo.currentTextChanged.connect(self.refresh_thought_list)
        self.new_button = QPushButton("新建轻思考", widget)
        self.new_button.clicked.connect(self.new_thought)
        self.delete_button = QPushButton("删除当前记录", widget)
        self.delete_button.clicked.connect(self.delete_current_thought)
        self.thought_list = QListWidget(widget)
        self.thought_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.type_filter_combo)
        layout.addWidget(self.status_filter_combo)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.thought_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_thought)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_thought)
        self.to_plan_button = QPushButton("转成轻计划", widget)
        self.to_plan_button.clicked.connect(self.convert_to_plan)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addWidget(self.to_plan_button)
        action_row.addStretch(1)

        info_group = QGroupBox("思考整理", widget)
        info_layout = QVBoxLayout(info_group)
        form = QFormLayout()
        self.title_input = QLineEdit(info_group)
        self.title_input.setPlaceholderText("标题 / 问题")
        self.title_input.textChanged.connect(self._mark_dirty)
        self.type_combo = QComboBox(info_group)
        self.type_combo.addItems(THOUGHT_TYPES)
        self.type_combo.currentTextChanged.connect(self._mark_dirty)
        self.status_combo = QComboBox(info_group)
        self.status_combo.addItems(THOUGHT_STATUSES)
        self.status_combo.currentTextChanged.connect(self._mark_dirty)
        form.addRow("标题 / 问题", self.title_input)
        form.addRow("类型", self.type_combo)
        form.addRow("状态", self.status_combo)
        info_layout.addLayout(form)

        self.description_edit = self._make_text_edit("描述：这个问题为什么冒出来？")
        self.conclusion_edit = self._make_text_edit("初步结论：现在先怎么判断？")
        self.notes_edit = self._make_text_edit("备注：关联日记、轻资源、自我分析的线索可以先写在这里。")
        info_layout.addWidget(QLabel("描述", info_group))
        info_layout.addWidget(self.description_edit)
        info_layout.addWidget(QLabel("初步结论", info_group))
        info_layout.addWidget(self.conclusion_edit)
        info_layout.addWidget(QLabel("备注", info_group))
        info_layout.addWidget(self.notes_edit)

        idea_group = QGroupBox("追加想法", widget)
        idea_layout = QVBoxLayout(idea_group)
        self.idea_list = QListWidget(idea_group)
        self.idea_input = QTextEdit(idea_group)
        self.idea_input.setPlaceholderText("写一条新想法，点击追加后会进入想法列表。")
        self.idea_input.setMinimumHeight(76)
        idea_buttons = QHBoxLayout()
        self.add_idea_button = QPushButton("追加想法", idea_group)
        self.add_idea_button.clicked.connect(self.append_idea)
        self.remove_idea_button = QPushButton("删除所选想法", idea_group)
        self.remove_idea_button.clicked.connect(self.remove_selected_idea)
        idea_buttons.addWidget(self.add_idea_button)
        idea_buttons.addWidget(self.remove_idea_button)
        idea_buttons.addStretch(1)
        idea_layout.addWidget(self.idea_list, 1)
        idea_layout.addWidget(self.idea_input)
        idea_layout.addLayout(idea_buttons)

        layout.addLayout(action_row)
        layout.addWidget(info_group, 2)
        layout.addWidget(idea_group, 1)
        return widget

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit(self)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(90)
        edit.textChanged.connect(self._mark_dirty)
        return edit

    def refresh_thought_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id or (self.current_thought.id if self.current_thought is not None else None)
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        thought_type = self.type_filter_combo.currentText() if hasattr(self, "type_filter_combo") else "全部"
        status = self.status_filter_combo.currentText() if hasattr(self, "status_filter_combo") else "全部"
        blocker = QSignalBlocker(self.thought_list)
        self.thought_list.clear()
        target_row = -1
        for row, thought in enumerate(self.storage.list_thoughts(query, thought_type, status)):
            item = QListWidgetItem(self._build_list_text(thought))
            item.setData(Qt.ItemDataRole.UserRole, thought.id)
            item.setToolTip(thought.description or thought.preliminary_conclusion or thought.display_title)
            self.thought_list.addItem(item)
            if current_id and thought.id == current_id:
                target_row = row
        if target_row >= 0:
            self.thought_list.setCurrentRow(target_row)
        del blocker
        if self.thought_list.count() == 0:
            self.thought_list.addItem("暂无轻思考记录。")

    def new_thought(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_thought())
        self.thought_list.blockSignals(True)
        self.thought_list.clearSelection()
        self.thought_list.blockSignals(False)
        self._show_status("已创建新的轻思考草稿。", 3000)

    def save_thought(self) -> bool:
        thought = self._read_form()
        try:
            saved = self.storage.save_thought(thought)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存轻思考时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_thought_list(select_id=saved.id)
        self._show_status("轻思考已保存。", 3000)
        return True

    def reload_current_thought(self) -> None:
        if self.current_thought is None or not self.storage.thought_dir(self.current_thought.id).exists():
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
        try:
            thought = self.storage.load_thought(self.current_thought.id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取轻思考时出错：\n{exc}")
            return
        self._fill_form(thought)
        self.refresh_thought_list(select_id=thought.id)

    def delete_current_thought(self) -> None:
        if self.current_thought is None:
            return
        if not self.storage.thought_dir(self.current_thought.id).exists():
            reply = QMessageBox.question(self, "放弃草稿", "这条轻思考还没保存，确定放弃吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self._discard_current_draft("已放弃未保存的轻思考草稿。")
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定删除这条轻思考吗？\n\n{self.current_thought.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_thought(self.current_thought.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除轻思考时出错：\n{exc}")
            return
        self._discard_current_draft("已删除当前轻思考。")

    def append_idea(self) -> None:
        if self.current_thought is None:
            self.current_thought = self.storage.create_empty_thought()
        text = self.idea_input.toPlainText().strip()
        if not text:
            return
        self.current_thought.ideas.append({"time": self.storage.create_empty_thought().created_at, "text": text})
        self.idea_input.clear()
        self._refresh_ideas()
        self._mark_dirty()

    def remove_selected_idea(self) -> None:
        if self.current_thought is None:
            return
        row = self.idea_list.currentRow()
        if row < 0 or row >= len(self.current_thought.ideas):
            return
        del self.current_thought.ideas[row]
        self._refresh_ideas()
        self._mark_dirty()

    def convert_to_plan(self) -> None:
        if self.current_thought is None:
            return
        thought = self._read_form()
        plan = self.plan_storage.create_empty_plan()
        plan.title = thought.display_title
        plan.notes = "\n\n".join(
            part
            for part in [
                f"来源轻思考：{thought.id}",
                thought.description,
                "想法列表：\n" + "\n".join(f"- {item.get('text', '')}" for item in thought.ideas),
                f"初步结论：{thought.preliminary_conclusion}" if thought.preliminary_conclusion else "",
                thought.notes,
            ]
            if part.strip()
        )
        saved_plan = self.plan_storage.save_plan(plan)
        thought.status = "已转计划"
        self.storage.save_thought(thought)
        self.plan_created.emit(saved_plan.id)
        self._show_status("已把轻思考转成轻计划。", 4000)

    def open_thought_by_id(self, thought_id: str, status_message: str | None = None) -> None:
        try:
            thought = self.storage.load_thought(thought_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取轻思考时出错：\n{exc}")
            return
        self._fill_form(thought)
        self.refresh_thought_list(select_id=thought.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _fill_form(self, thought: ThoughtEntry) -> None:
        self._is_loading_form = True
        self.current_thought = thought
        try:
            self.title_input.setText(thought.title)
            self._set_combo_text(self.type_combo, thought.thought_type)
            self._set_combo_text(self.status_combo, thought.status)
            self.description_edit.setPlainText(thought.description)
            self.conclusion_edit.setPlainText(thought.preliminary_conclusion)
            self.notes_edit.setPlainText(thought.notes)
            self.idea_input.clear()
            self._refresh_ideas()
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> ThoughtEntry:
        if self.current_thought is None:
            self.current_thought = self.storage.create_empty_thought()
        self.current_thought.title = self.title_input.text().strip()
        self.current_thought.thought_type = self.type_combo.currentText().strip() or "其他"
        self.current_thought.status = self.status_combo.currentText().strip() or "思考中"
        self.current_thought.description = self.description_edit.toPlainText()
        self.current_thought.preliminary_conclusion = self.conclusion_edit.toPlainText()
        self.current_thought.notes = self.notes_edit.toPlainText()
        return self.current_thought

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        thought_id = current.data(Qt.ItemDataRole.UserRole)
        if not thought_id:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.thought_list)
            self.thought_list.setCurrentItem(previous)
            del blocker
            return
        if self.current_thought is not None and self.current_thought.id == thought_id:
            return
        self.open_thought_by_id(thought_id, status_message="已打开这条轻思考。")

    def _refresh_ideas(self) -> None:
        self.idea_list.clear()
        for idea in self.current_thought.ideas if self.current_thought else []:
            self.idea_list.addItem(f"{idea.get('time', '')}\n{idea.get('text', '')}")

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_thought = None
        self._set_dirty(False)
        self.refresh_thought_list()
        if self.thought_list.count() > 0 and self.thought_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.thought_list.setCurrentRow(0)
        else:
            self.new_thought()
        self._show_status(status_message, 3000)

    def _build_list_text(self, thought: ThoughtEntry) -> str:
        return f"{thought.display_title}\n{thought.thought_type} | {thought.status}"

    def _set_combo_text(self, combo: QComboBox, text: str) -> None:
        index = combo.findText(text)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _mark_dirty(self, *_args) -> None:
        if self._is_loading_form:
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
        return self.save_thought()

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_thought is None:
            return False
        if self.storage.thought_dir(self.current_thought.id).exists():
            return True
        return bool(
            self.title_input.text().strip()
            or self.description_edit.toPlainText().strip()
            or self.conclusion_edit.toPlainText().strip()
            or self.notes_edit.toPlainText().strip()
            or self.current_thought.ideas
        )

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
