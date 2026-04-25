from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QComboBox,
)

from .book_storage import BookStorage
from .exchange import ExchangePackageExporter
from .models import BookEntry, BookImageDraft, BookRelatedDiary
from .storage import DiaryStorage
from .ui_helpers import make_scroll_area


class DiaryPickerDialog(QDialog):
    def __init__(self, diary_storage: DiaryStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.diary_storage = diary_storage
        self.setWindowTitle("选择要关联的日记")
        self.resize(420, 420)

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜索日期 / 标题 / 正文")
        self.search_input.textChanged.connect(self._refresh_list)

        self.entry_list = QListWidget(self)
        self.entry_list.itemDoubleClicked.connect(lambda _item: self.accept())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self.search_input)
        layout.addWidget(self.entry_list, 1)
        layout.addWidget(buttons)

        self._refresh_list()

    def selected_relation(self) -> BookRelatedDiary | None:
        item = self.entry_list.currentItem()
        if item is None:
            return None
        payload = item.data(Qt.ItemDataRole.UserRole)
        return BookRelatedDiary(
            entry_id=str(payload["entry_id"]),
            date=str(payload["date"]),
            title=str(payload["title"]),
        )

    def accept(self) -> None:  # type: ignore[override]
        if self.selected_relation() is None:
            QMessageBox.information(self, "先选一篇日记", "请先选择要关联的日记。")
            return
        super().accept()

    def _refresh_list(self) -> None:
        query = self.search_input.text()
        blocker = QSignalBlocker(self.entry_list)
        self.entry_list.clear()

        for entry in self.diary_storage.list_entries(query):
            item = QListWidgetItem(f"{entry.date} | {entry.display_title}")
            item.setToolTip(entry.body[:150] or entry.display_title)
            item.setData(
                Qt.ItemDataRole.UserRole,
                {
                    "entry_id": entry.id,
                    "date": entry.date,
                    "title": entry.display_title,
                },
            )
            self.entry_list.addItem(item)

        if self.entry_list.count() > 0:
            self.entry_list.setCurrentRow(0)
        del blocker


class BookPage(QWidget):
    dirty_state_changed = Signal(bool)
    open_diary_requested = Signal(str, str)

    def __init__(
        self,
        storage: BookStorage,
        diary_storage: DiaryStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.diary_storage = diary_storage
        self.current_book: BookEntry | None = None
        self.image_items: list[BookImageDraft] = []
        self.is_dirty = False
        self._is_loading_form = False
        self._is_loading_image_details = False
        self._build_ui()
        self.refresh_book_list()
        if self.book_list.count() > 0:
            self.book_list.setCurrentRow(0)
        else:
            self.new_book()

    def has_unsaved_changes(self) -> bool:
        return self.is_dirty

    def maybe_finish_pending_changes(self) -> bool:
        return self._maybe_keep_changes()

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

        title = QLabel("读书笔记", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索书名 / 作者 / 标签 / 笔记")
        self.search_input.textChanged.connect(self.refresh_book_list)

        self.new_button = QPushButton("新建读书笔记", widget)
        self.new_button.clicked.connect(self.new_book)

        self.delete_button = QPushButton("删除当前读书笔记", widget)
        self.delete_button.clicked.connect(self.delete_current_book)

        self.export_package_button = QPushButton("导出读书压缩包", widget)
        self.export_package_button.clicked.connect(self.export_book_package)

        self.book_list = QListWidget(widget)
        self.book_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.export_package_button)
        layout.addWidget(self.book_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_book)

        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_book)

        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addStretch(1)

        info_group = QGroupBox("书籍信息与笔记", widget)
        info_layout = QVBoxLayout(info_group)

        form = QFormLayout()
        self.title_input = QLineEdit(info_group)
        self.title_input.setPlaceholderText("书名")
        self.title_input.textChanged.connect(self._mark_dirty)

        self.author_input = QLineEdit(info_group)
        self.author_input.setPlaceholderText("作者")
        self.author_input.textChanged.connect(self._mark_dirty)

        self.status_combo = QComboBox(info_group)
        self.status_combo.addItems(["想读", "在读", "读完"])
        self.status_combo.currentTextChanged.connect(self._mark_dirty)

        self.start_date_input = QLineEdit(info_group)
        self.start_date_input.setPlaceholderText("yyyy-MM-dd，可留空")
        self.start_date_input.textChanged.connect(self._mark_dirty)

        self.finish_date_input = QLineEdit(info_group)
        self.finish_date_input.setPlaceholderText("yyyy-MM-dd，可留空")
        self.finish_date_input.textChanged.connect(self._mark_dirty)

        self.tags_input = QLineEdit(info_group)
        self.tags_input.setPlaceholderText("多个标签用逗号分隔")
        self.tags_input.textChanged.connect(self._mark_dirty)

        form.addRow("书名", self.title_input)
        form.addRow("作者", self.author_input)
        form.addRow("阅读状态", self.status_combo)
        form.addRow("开始日期", self.start_date_input)
        form.addRow("完成日期", self.finish_date_input)
        form.addRow("标签", self.tags_input)

        summary_label = QLabel("阅读摘要", info_group)
        self.summary_edit = QTextEdit(info_group)
        self.summary_edit.setPlaceholderText("简要记录这本书讲了什么，以及它为什么值得记。")
        self.summary_edit.setMinimumHeight(120)
        self.summary_edit.textChanged.connect(self._mark_dirty)

        notes_label = QLabel("读书笔记正文", info_group)
        self.notes_edit = QTextEdit(info_group)
        self.notes_edit.setPlaceholderText("这里写你自己的读书感受、摘记和理解，重点是“书和你的关系”。")
        self.notes_edit.setMinimumHeight(260)
        self.notes_edit.textChanged.connect(self._mark_dirty)

        info_layout.addLayout(form)
        info_layout.addWidget(summary_label)
        info_layout.addWidget(self.summary_edit)
        info_layout.addWidget(notes_label)
        info_layout.addWidget(self.notes_edit, 1)

        lower_splitter = QSplitter(Qt.Orientation.Horizontal, widget)
        lower_splitter.setMinimumHeight(300)
        lower_splitter.addWidget(self._build_image_group())
        lower_splitter.addWidget(self._build_related_group())
        lower_splitter.setChildrenCollapsible(False)
        lower_splitter.setSizes([520, 360])

        right_splitter = QSplitter(Qt.Orientation.Vertical, widget)
        right_splitter.addWidget(info_group)
        right_splitter.addWidget(lower_splitter)
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 0)
        right_splitter.setSizes([460, 320])

        layout.addLayout(action_row)
        layout.addWidget(right_splitter, 1)
        return widget

    def _build_image_group(self) -> QWidget:
        group = QGroupBox("书封 / 书籍图片", self)
        layout = QHBoxLayout(group)

        left = QVBoxLayout()
        self.image_list = QListWidget(group)
        self.image_list.currentItemChanged.connect(self._on_image_selection_changed)

        button_row = QHBoxLayout()
        self.add_image_button = QPushButton("添加书封/图片", group)
        self.add_image_button.clicked.connect(self.add_images)

        self.open_image_button = QPushButton("打开所选图片", group)
        self.open_image_button.clicked.connect(self.open_selected_image)

        self.remove_image_button = QPushButton("移除所选图片", group)
        self.remove_image_button.clicked.connect(self.remove_selected_image)

        button_row.addWidget(self.add_image_button)
        button_row.addWidget(self.open_image_button)
        button_row.addWidget(self.remove_image_button)

        self.image_label_input = QLineEdit(group)
        self.image_label_input.setPlaceholderText("图片备注（可选）")
        self.image_label_input.textChanged.connect(self._update_selected_image_label)

        note = QLabel("第一张图通常可以当作书封，也可以继续补充其它书籍图片。", group)
        note.setWordWrap(True)
        note.setStyleSheet("color: #666666;")

        left.addWidget(self.image_list, 1)
        left.addLayout(button_row)
        left.addWidget(self.image_label_input)
        left.addWidget(note)

        self.image_preview = QLabel("未选择图片", group)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(220, 180)
        self.image_preview.setStyleSheet(
            "border: 1px solid #cccccc; background: #fafafa; color: #666666;",
        )

        layout.addLayout(left, 2)
        layout.addWidget(self.image_preview, 1)
        return group

    def _build_related_group(self) -> QWidget:
        group = QGroupBox("关联日记", self)
        layout = QVBoxLayout(group)

        note = QLabel("可以关联若干篇日记，方便把“读这本书时的生活记录”串起来。", group)
        note.setWordWrap(True)
        note.setStyleSheet("color: #666666;")

        action_row = QHBoxLayout()
        self.add_related_button = QPushButton("关联一篇日记", group)
        self.add_related_button.clicked.connect(self.add_related_diary)

        self.remove_related_button = QPushButton("移除所选关联", group)
        self.remove_related_button.clicked.connect(self.remove_selected_related_diary)

        self.open_related_button = QPushButton("打开所选日记", group)
        self.open_related_button.clicked.connect(self.open_selected_related_diary)

        action_row.addWidget(self.add_related_button)
        action_row.addWidget(self.remove_related_button)
        action_row.addWidget(self.open_related_button)

        self.related_list = QListWidget(group)
        self.related_list.currentItemChanged.connect(self._update_related_buttons)

        layout.addWidget(note)
        layout.addLayout(action_row)
        layout.addWidget(self.related_list, 1)
        return group

    def refresh_book_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id
        if current_id is None and self.current_book is not None:
            current_id = self.current_book.id

        query = self.search_input.text() if hasattr(self, "search_input") else ""
        blocker = QSignalBlocker(self.book_list)
        self.book_list.clear()

        target_row = -1
        for row, book in enumerate(self.storage.list_books(query)):
            item = QListWidgetItem(self._build_book_list_text(book))
            item.setData(Qt.ItemDataRole.UserRole, book.id)
            item.setToolTip(book.summary[:150] or book.display_title)
            self.book_list.addItem(item)
            if current_id and book.id == current_id:
                target_row = row

        if target_row >= 0:
            self.book_list.setCurrentRow(target_row)
        del blocker

    def new_book(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_book())
        self.book_list.blockSignals(True)
        self.book_list.clearSelection()
        self.book_list.blockSignals(False)
        self._show_status("已创建新的读书笔记草稿。", 3000)

    def save_book(self) -> None:
        book = self._read_form()
        try:
            saved = self.storage.save_book(book, self.image_items)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存读书笔记时出错：\n{exc}")
            return

        self._fill_form(saved)
        self.refresh_book_list(select_id=saved.id)
        self._show_status("已保存读书笔记到本地。", 3000)

    def reload_current_book(self) -> None:
        if self.current_book is None:
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
        if self.current_book.id and self.storage.book_dir(self.current_book.id).exists():
            try:
                book = self.storage.load_book(self.current_book.id)
            except Exception as exc:
                QMessageBox.critical(self, "读取失败", f"恢复已保存内容时出错：\n{exc}")
                return
            self._fill_form(book)
            self.refresh_book_list(select_id=book.id)
            self._show_status("已恢复到上次保存的读书笔记内容。", 3000)

    def delete_current_book(self) -> None:
        if self.current_book is None:
            return

        if not self.storage.book_dir(self.current_book.id).exists():
            reply = QMessageBox.question(
                self,
                "放弃草稿",
                "这篇读书笔记草稿还没有保存，确定要放弃吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._discard_current_draft("已放弃未保存的读书笔记草稿。")
            return

        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定要删除这篇读书笔记吗？\n\n{self.current_book.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        book_id = self.current_book.id
        try:
            self.storage.delete_book(book_id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除读书笔记时出错：\n{exc}")
            return

        self.current_book = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_book_list()

        if self.book_list.count() > 0:
            self.book_list.setCurrentRow(0)
        else:
            self.new_book()

        self._show_status("已删除当前读书笔记。", 3000)

    def export_book_package(self) -> None:
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "选择读书压缩包导出目录",
            str((self.storage.root_dir / "exports").resolve()),
        )
        if not export_dir:
            return

        try:
            zip_path = ExchangePackageExporter(self.storage.root_dir).export_module("book", export_dir)
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", f"导出读书压缩包时出错：\n{exc}")
            return

        QMessageBox.information(self, "导出完成", f"读书压缩包已生成：\n\n{zip_path}")
        self._show_status("已导出读书压缩包。", 5000)

    def add_related_diary(self) -> None:
        dialog = DiaryPickerDialog(self.diary_storage, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        relation = dialog.selected_relation()
        if relation is None:
            return

        if self.current_book is None:
            self.current_book = self.storage.create_empty_book()

        existing_ids = {item.entry_id for item in self.current_book.related_diaries}
        if relation.entry_id in existing_ids:
            QMessageBox.information(self, "已关联过", "这篇日记已经关联过了。")
            return

        self.current_book.related_diaries.append(relation)
        self._refresh_related_list(select_entry_id=relation.entry_id)
        self._mark_dirty()
        self._show_status("已关联一篇日记，保存后生效。", 3000)

    def remove_selected_related_diary(self) -> None:
        relation = self._current_related_diary()
        if relation is None or self.current_book is None:
            return

        remaining = [item for item in self.current_book.related_diaries if item.entry_id != relation.entry_id]
        self.current_book.related_diaries = remaining
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
            self.image_items.append(BookImageDraft(source_path=path, label=""))
            existing.add(normalized)
            added_count += 1

        if added_count == 0:
            return

        self._refresh_image_list(select_row=len(self.image_items) - 1)
        self._mark_dirty()
        self._show_status(f"已加入 {added_count} 张书封/书籍图片，保存后生效。", 3000)

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

    def _fill_form(self, book: BookEntry) -> None:
        self._is_loading_form = True
        self.current_book = book
        self.image_items = [
            BookImageDraft(
                source_path=self.storage.resolve_image_path(book.id, image.file_name),
                label=image.label,
            )
            for image in book.images
        ]

        try:
            self.title_input.setText(book.title)
            self.author_input.setText(book.author)
            self._set_status(book.status)
            self.start_date_input.setText(book.start_date)
            self.finish_date_input.setText(book.finish_date)
            self.tags_input.setText(", ".join(book.tags))
            self.summary_edit.setPlainText(book.summary)
            self.notes_edit.setPlainText(book.notes)
            self._refresh_image_list()
            self._refresh_related_list()
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> BookEntry:
        if self.current_book is None:
            self.current_book = self.storage.create_empty_book()

        tags = [
            item.strip()
            for item in self.tags_input.text().replace("，", ",").split(",")
            if item.strip()
        ]

        self.current_book.title = self.title_input.text().strip()
        self.current_book.author = self.author_input.text().strip()
        self.current_book.status = self.status_combo.currentText().strip() or "想读"
        self.current_book.start_date = self.start_date_input.text().strip()
        self.current_book.finish_date = self.finish_date_input.text().strip()
        self.current_book.tags = tags
        self.current_book.summary = self.summary_edit.toPlainText()
        self.current_book.notes = self.notes_edit.toPlainText()
        return self.current_book

    def _open_book_by_id(self, book_id: str, status_message: str | None = None) -> None:
        try:
            book = self.storage.load_book(book_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取读书笔记时出错：\n{exc}")
            return

        self._fill_form(book)
        self.refresh_book_list(select_id=book.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_book = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_book_list()

        if self.book_list.count() > 0:
            self.book_list.setCurrentRow(0)
        else:
            self.new_book()

        self._show_status(status_message, 3000)

    def _on_current_item_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.book_list)
            self.book_list.setCurrentItem(previous)
            del blocker
            return

        book_id = current.data(Qt.ItemDataRole.UserRole)
        if self.current_book is not None and self.current_book.id == book_id:
            return
        self._open_book_by_id(book_id, status_message="已重新打开这篇读书笔记。")

    def _refresh_related_list(self, select_entry_id: str | None = None) -> None:
        blocker = QSignalBlocker(self.related_list)
        self.related_list.clear()

        target_row = -1
        for row, relation in enumerate(self.current_book.related_diaries if self.current_book is not None else []):
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

    def _current_related_diary(self) -> BookRelatedDiary | None:
        if self.current_book is None:
            return None
        entry_id = self.related_list.currentItem().data(Qt.ItemDataRole.UserRole) if self.related_list.currentItem() else None
        if not entry_id:
            return None
        for relation in self.current_book.related_diaries:
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
            label = image_item.label.strip() or ("书封" if index == 1 else f"图片 {index}")
            if not self._is_current_book_image(image_item.source_path):
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

    def _is_current_book_image(self, image_path: Path) -> bool:
        if self.current_book is None:
            return False
        return image_path.parent == self.storage.image_dir(self.current_book.id)

    def _set_status(self, status: str) -> None:
        index = self.status_combo.findText(status)
        if index < 0:
            index = 0
        self.status_combo.setCurrentIndex(index)

    def _build_book_list_text(self, book: BookEntry) -> str:
        subtitle_parts = [book.status]
        if book.author.strip():
            subtitle_parts.append(book.author.strip())
        return f"{book.display_title}\n{' | '.join(subtitle_parts)}"

    def _mark_dirty(self, *_args) -> None:
        if self._is_loading_form or self._is_loading_image_details:
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
            "当前读书笔记有未保存内容，是否先保存？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_book()
            return not self.is_dirty
        if reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
