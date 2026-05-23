from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
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
from .note_storage import NoteEntry, NoteStorage
from .ui_helpers import make_scroll_area


class NotePage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)

    def __init__(self, storage: NoteStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.storage = storage
        self.current_note: NoteEntry | None = None
        self.is_dirty = False
        self._is_loading_form = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_note_list()
        if self.note_list.count() > 0 and self.note_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.note_list.setCurrentRow(0)
        else:
            self.new_note()

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

        title = QLabel("笔记", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 描述 / 正文")
        self.search_input.textChanged.connect(self.refresh_note_list)
        self.new_button = QPushButton("新建笔记", widget)
        self.new_button.clicked.connect(self.new_note)
        self.delete_button = QPushButton("删除当前笔记", widget)
        self.delete_button.clicked.connect(self.delete_current_note)
        self.note_list = QListWidget(widget)
        self.note_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.note_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_note)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_note)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addStretch(1)

        self.title_input = QLineEdit(widget)
        self.title_input.setPlaceholderText("标题")
        self.title_input.setStyleSheet("font-size: 16px; font-weight: 600; padding: 8px;")
        self.title_input.textChanged.connect(self._mark_dirty)

        self.description_edit = QTextEdit(widget)
        self.description_edit.setPlaceholderText("简单描述")
        self.description_edit.setMaximumHeight(100)
        self.description_edit.textChanged.connect(self._mark_dirty)

        self.body_edit = QTextEdit(widget)
        self.body_edit.setPlaceholderText("正文")
        self.body_edit.textChanged.connect(self._mark_dirty)

        layout.addLayout(action_row)
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("简单描述", widget))
        layout.addWidget(self.description_edit)
        layout.addWidget(QLabel("正文", widget))
        layout.addWidget(self.body_edit, 1)
        return widget

    def refresh_note_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id or (self.current_note.id if self.current_note is not None else None)
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        blocker = QSignalBlocker(self.note_list)
        self.note_list.clear()
        target_row = -1
        for row, note in enumerate(self.storage.list_notes(query)):
            item = QListWidgetItem(self._build_list_text(note))
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            item.setToolTip(note.description or note.body[:80] if note.body else note.display_title)
            self.note_list.addItem(item)
            if current_id and note.id == current_id:
                target_row = row
        if target_row >= 0:
            self.note_list.setCurrentRow(target_row)
        del blocker
        if self.note_list.count() == 0:
            self.note_list.addItem("暂无笔记。")

    def new_note(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_note())
        self.note_list.blockSignals(True)
        self.note_list.clearSelection()
        self.note_list.blockSignals(False)
        self._show_status("已创建新的笔记草稿。", 3000)

    def save_note(self) -> bool:
        note = self._read_form()
        try:
            saved = self.storage.save_note(note)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存笔记时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_note_list(select_id=saved.id)
        self._show_status("笔记已保存。", 3000)
        return True

    def reload_current_note(self) -> None:
        if self.current_note is None or not self.storage.note_dir(self.current_note.id).exists():
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
            note = self.storage.load_note(self.current_note.id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取笔记时出错：\n{exc}")
            return
        self._fill_form(note)
        self.refresh_note_list(select_id=note.id)

    def delete_current_note(self) -> None:
        if self.current_note is None:
            return
        if not self.storage.note_dir(self.current_note.id).exists():
            reply = QMessageBox.question(self, "放弃草稿", "这条笔记还没保存，确定放弃吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self._discard_current_draft("已放弃未保存的笔记草稿。")
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定删除这条笔记吗？\n\n{self.current_note.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_note(self.current_note.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除笔记时出错：\n{exc}")
            return
        self._discard_current_draft("已删除当前笔记。")

    def open_note_by_id(self, note_id: str, status_message: str | None = None) -> None:
        try:
            note = self.storage.load_note(note_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取笔记时出错：\n{exc}")
            return
        self._fill_form(note)
        self.refresh_note_list(select_id=note.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _fill_form(self, note: NoteEntry) -> None:
        self._is_loading_form = True
        self.current_note = note
        try:
            self.title_input.setText(note.title)
            self.description_edit.setPlainText(note.description)
            self.body_edit.setPlainText(note.body)
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> NoteEntry:
        if self.current_note is None:
            self.current_note = self.storage.create_empty_note()
        self.current_note.title = self.title_input.text().strip()
        self.current_note.description = self.description_edit.toPlainText()
        self.current_note.body = self.body_edit.toPlainText()
        return self.current_note

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        note_id = current.data(Qt.ItemDataRole.UserRole)
        if not note_id:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.note_list)
            self.note_list.setCurrentItem(previous)
            del blocker
            return
        if self.current_note is not None and self.current_note.id == note_id:
            return
        self.open_note_by_id(note_id, status_message="已打开这条笔记。")

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_note = None
        self._set_dirty(False)
        self.refresh_note_list()
        if self.note_list.count() > 0 and self.note_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.note_list.setCurrentRow(0)
        else:
            self.new_note()
        self._show_status(status_message, 3000)

    def _build_list_text(self, note: NoteEntry) -> str:
        preview = (note.description or note.body)[:50] if (note.description or note.body) else ""
        if preview:
            return f"{note.display_title}\n{preview}"
        return note.display_title

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
        note = self._read_form()
        try:
            self.storage.save_note(note)
        except Exception:
            return False
        self._set_dirty(False)
        return True

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_note is None:
            return False
        if self.storage.note_dir(self.current_note.id).exists():
            return True
        return bool(self.title_input.text().strip() or self.description_edit.toPlainText().strip() or self.body_edit.toPlainText().strip())

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
