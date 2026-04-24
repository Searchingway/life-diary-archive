from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, QSignalBlocker, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDateEdit,
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
    QProgressDialog,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .exporters import DiaryExportItem, DiaryExporter
from .footprint_storage import FootprintStorage
from .models import DiaryEntry, DiaryImageDraft
from .storage import DiaryStorage


class ExportRangeDialog(QDialog):
    def __init__(
        self,
        min_date: QDate,
        max_date: QDate,
        initial_date: QDate,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("选择导出时间范围")
        self.resize(360, 160)

        layout = QVBoxLayout(self)

        note = QLabel("选择开始和结束日期。导出时会按旧日期在前排序，每篇日记另起一页。", self)
        note.setWordWrap(True)

        form = QFormLayout()
        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.setDateRange(min_date, max_date)
        self.start_date_edit.setDate(initial_date)

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.setDateRange(min_date, max_date)
        self.end_date_edit.setDate(initial_date)

        form.addRow("开始日期", self.start_date_edit)
        form.addRow("结束日期", self.end_date_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(note)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:  # type: ignore[override]
        if self.start_date_edit.date() > self.end_date_edit.date():
            QMessageBox.warning(self, "日期范围无效", "开始日期不能晚于结束日期。")
            return
        super().accept()


class DiaryPage(QWidget):
    dirty_state_changed = Signal(bool)
    show_footprints_requested = Signal(str)

    def __init__(
        self,
        storage: DiaryStorage,
        footprint_storage: FootprintStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.footprint_storage = footprint_storage
        self.current_entry: DiaryEntry | None = None
        self.image_items: list[DiaryImageDraft] = []
        self.is_dirty = False
        self._is_loading_form = False
        self._is_loading_image_details = False
        self._build_ui()
        self.refresh_list()
        if self.entry_list.count() > 0:
            self.entry_list.setCurrentRow(0)
        else:
            self.new_entry()

    def has_unsaved_changes(self) -> bool:
        return self.is_dirty

    def maybe_finish_pending_changes(self) -> bool:
        return self._maybe_keep_changes()

    def open_first_entry_for_date(self, target_date: str) -> bool | None:
        items = self.storage.list_entries_by_date(target_date)
        if not items:
            return False
        if not self._maybe_keep_changes():
            return None

        blocker = QSignalBlocker(self.search_input)
        self.search_input.setText(target_date)
        del blocker
        self.refresh_list(select_id=items[0].id)
        self._open_entry_by_id(items[0].id, status_message=f"已定位到 {target_date} 的日记。")
        return True

    def open_entry_by_id(self, entry_id: str) -> bool | None:
        entry_dir = self.storage.entry_dir(entry_id)
        if not entry_dir.exists():
            return False
        if not self._maybe_keep_changes():
            return None

        blocker = QSignalBlocker(self.search_input)
        self.search_input.clear()
        del blocker
        self.refresh_list(select_id=entry_id)
        self._open_entry_by_id(entry_id, status_message="已定位到关联日记。")
        return True

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_editor())
        splitter.setSizes([280, 760])

        layout.addWidget(splitter)

    def _build_sidebar(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("日记列表", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索日期 / 标题 / 正文")
        self.search_input.textChanged.connect(self.refresh_list)

        self.new_button = QPushButton("新建日记", widget)
        self.new_button.clicked.connect(self.new_entry)

        self.delete_button = QPushButton("删除当前日记", widget)
        self.delete_button.clicked.connect(self.delete_current_entry)

        self.entry_list = QListWidget(widget)
        self.entry_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.entry_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()

        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_entry)

        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_entry)

        self.insert_image_button = QPushButton("插入图片", widget)
        self.insert_image_button.clicked.connect(self.add_images)

        self.export_button = QPushButton("导出 Word / PDF", widget)
        self.export_button.clicked.connect(self.export_current_entry)

        self.show_footprints_button = QPushButton("查看当天足迹", widget)
        self.show_footprints_button.clicked.connect(self._emit_show_footprints_requested)

        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addWidget(self.insert_image_button)
        action_row.addWidget(self.export_button)
        action_row.addWidget(self.show_footprints_button)
        action_row.addStretch(1)

        form = QFormLayout()
        self.date_edit = QDateEdit(widget)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.dateChanged.connect(self._on_date_changed)

        self.title_input = QLineEdit(widget)
        self.title_input.setPlaceholderText("标题可选")
        self.title_input.textChanged.connect(self._mark_dirty)

        form.addRow("日期", self.date_edit)
        form.addRow("标题", self.title_input)

        relation_row = QHBoxLayout()
        self.footprint_hint_label = QLabel("当天足迹：0 条", widget)
        relation_row.addWidget(self.footprint_hint_label)
        relation_row.addStretch(1)

        body_label = QLabel("正文", widget)
        self.body_edit = QTextEdit(widget)
        self.body_edit.setPlaceholderText("先把第一篇日记写起来。")
        self.body_edit.textChanged.connect(self._mark_dirty)

        image_group = QGroupBox("已插入图片", widget)
        image_group_layout = QHBoxLayout(image_group)

        image_left = QVBoxLayout()
        self.image_list = QListWidget(image_group)
        self.image_list.currentItemChanged.connect(self._on_image_selection_changed)

        image_button_row = QHBoxLayout()
        self.open_image_button = QPushButton("打开所选图片", image_group)
        self.open_image_button.clicked.connect(self.open_selected_image)

        self.remove_image_button = QPushButton("移除所选图片", image_group)
        self.remove_image_button.clicked.connect(self.remove_selected_image)

        image_button_row.addWidget(self.open_image_button)
        image_button_row.addWidget(self.remove_image_button)

        self.image_label_input = QLineEdit(image_group)
        self.image_label_input.setPlaceholderText("图片备注（可选，导出时显示）")
        self.image_label_input.textChanged.connect(self._update_selected_image_label)

        image_left.addWidget(self.image_list, 1)
        image_left.addLayout(image_button_row)
        image_left.addWidget(self.image_label_input)

        self.image_preview = QLabel("未选择图片", image_group)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(260, 180)
        self.image_preview.setStyleSheet(
            "border: 1px solid #cccccc; background: #fafafa; color: #666666;",
        )

        image_group_layout.addLayout(image_left, 2)
        image_group_layout.addWidget(self.image_preview, 1)

        layout.addLayout(action_row)
        layout.addLayout(form)
        layout.addLayout(relation_row)
        layout.addWidget(body_label)
        layout.addWidget(self.body_edit, 1)
        layout.addWidget(image_group)
        return widget

    def refresh_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id
        if current_id is None and self.current_entry is not None:
            current_id = self.current_entry.id

        query = self.search_input.text() if hasattr(self, "search_input") else ""
        blocker = QSignalBlocker(self.entry_list)
        self.entry_list.clear()

        target_row = -1
        for row, entry in enumerate(self.storage.list_entries(query)):
            item = QListWidgetItem(f"{entry.date} | {entry.display_title}")
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            item.setToolTip(entry.body[:150] or entry.display_title)
            self.entry_list.addItem(item)
            if current_id and entry.id == current_id:
                target_row = row

        if target_row >= 0:
            self.entry_list.setCurrentRow(target_row)
        del blocker

    def new_entry(self) -> None:
        if not self._maybe_keep_changes():
            return
        self.current_entry = self.storage.create_empty_entry()
        self._fill_form(self.current_entry)
        self.entry_list.blockSignals(True)
        self.entry_list.clearSelection()
        self.entry_list.blockSignals(False)
        self._show_status("已创建新的日记草稿。", 3000)

    def save_entry(self) -> None:
        entry = self._read_form()
        try:
            saved = self.storage.save_entry(entry, self.image_items)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存日记时出错：\n{exc}")
            return

        self.current_entry = saved
        self.refresh_list(select_id=saved.id)
        self._fill_form(saved)
        self._show_status("已保存到本地。", 3000)

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
            self.image_items.append(DiaryImageDraft(source_path=path, label=""))
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

    def delete_current_entry(self) -> None:
        if self.current_entry is None:
            return

        if not self.storage.entry_dir(self.current_entry.id).exists():
            reply = QMessageBox.question(
                self,
                "放弃草稿",
                "这篇日记草稿还没有保存，确定要放弃吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._discard_current_draft("已放弃未保存的日记草稿。")
            return

        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定要删除这篇日记吗？\n\n{self.current_entry.date} - {self.current_entry.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        entry_id = self.current_entry.id
        try:
            self.storage.delete_entry(entry_id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除日记时出错：\n{exc}")
            return

        self.current_entry = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_list()

        if self.entry_list.count() > 0:
            self.entry_list.setCurrentRow(0)
        else:
            self.new_entry()

        self._show_status("已删除当前日记。", 3000)

    def export_current_entry(self) -> None:
        if self.current_entry is None:
            return

        save_first = QMessageBox.question(
            self,
            "导出前保存",
            "导出前会先保存当前日记内容，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if save_first != QMessageBox.StandardButton.Yes:
            return

        self.save_entry()
        if self.is_dirty or self.current_entry is None:
            return

        available_entries = self.storage.list_entries()
        if not available_entries:
            QMessageBox.information(self, "暂无可导出内容", "当前没有可导出的日记。")
            return

        min_date = QDate.fromString(min(entry.date for entry in available_entries), "yyyy-MM-dd")
        max_date = QDate.fromString(max(entry.date for entry in available_entries), "yyyy-MM-dd")
        current_date = QDate.fromString(self.current_entry.date, "yyyy-MM-dd")
        if not current_date.isValid():
            current_date = max_date

        range_dialog = ExportRangeDialog(min_date, max_date, current_date, self)
        if range_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        start_date = range_dialog.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = range_dialog.end_date_edit.date().toString("yyyy-MM-dd")
        export_entries = self.storage.list_entries_in_date_range(start_date, end_date)
        if not export_entries:
            QMessageBox.information(self, "没有匹配日记", "所选时间范围内没有可导出的日记。")
            return

        export_dir = QFileDialog.getExistingDirectory(
            self,
            "选择导出目录",
            str((self.storage.root_dir / "exports").resolve()),
        )
        if not export_dir:
            return

        progress = QProgressDialog("准备导出", "", 0, 100, self)
        progress.setWindowTitle("导出进度")
        progress.setCancelButton(None)
        progress.setAutoClose(True)
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setValue(0)
        progress.show()

        exporter = DiaryExporter(export_dir)
        export_items = self._build_export_items(export_entries)

        def update_progress(value: int, message: str) -> None:
            progress.setLabelText(message)
            progress.setValue(value)
            QApplication.processEvents()

        try:
            docx_path, pdf_path = exporter.export_entries_word_and_pdf(
                export_items,
                progress=update_progress,
            )
        except Exception as exc:
            progress.close()
            QMessageBox.critical(self, "导出失败", f"导出 Word / PDF 时出错：\n{exc}")
            return

        progress.setValue(100)
        QMessageBox.information(
            self,
            "导出完成",
            f"已导出 {len(export_entries)} 篇日记：\n\n"
            f"Word：{docx_path}\n"
            f"PDF：{pdf_path}",
        )
        self._show_status("已导出 Word 和 PDF。", 5000)

    def reload_current_entry(self) -> None:
        if self.current_entry is None:
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
        if self.current_entry.id and self.storage.entry_dir(self.current_entry.id).exists():
            try:
                entry = self.storage.load_entry(self.current_entry.id)
            except Exception as exc:
                QMessageBox.critical(self, "读取失败", f"恢复已保存内容时出错：\n{exc}")
                return
            self.current_entry = entry
            self._fill_form(entry)
            self.refresh_list(select_id=entry.id)
            self._show_status("已恢复到上次保存的内容。", 3000)

    def _fill_form(self, entry: DiaryEntry) -> None:
        self._is_loading_form = True
        date_value = QDate.fromString(entry.date, "yyyy-MM-dd")
        if not date_value.isValid():
            date_value = QDate.currentDate()

        try:
            self.date_edit.setDate(date_value)
            self.title_input.setText(entry.title)
            self.body_edit.setPlainText(entry.body)
            self.image_items = [
                DiaryImageDraft(
                    source_path=self.storage.resolve_image_path(entry.id, image.file_name),
                    label=image.label,
                )
                for image in entry.images
            ]
            self._refresh_image_list()
            self._set_dirty(False)
            self._refresh_footprint_relation()
        finally:
            self._is_loading_form = False

    def _read_form(self) -> DiaryEntry:
        if self.current_entry is None:
            self.current_entry = self.storage.create_empty_entry()

        self.current_entry.date = self.date_edit.date().toString("yyyy-MM-dd")
        self.current_entry.title = self.title_input.text().strip()
        self.current_entry.body = self.body_edit.toPlainText()
        return self.current_entry

    def _open_entry_by_id(self, entry_id: str, status_message: str | None = None) -> None:
        try:
            entry = self.storage.load_entry(entry_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取日记时出错：\n{exc}")
            return

        self.current_entry = entry
        self._fill_form(entry)
        self.refresh_list(select_id=entry.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_entry = None
        self.image_items = []
        self._set_dirty(False)
        self.refresh_list()

        if self.entry_list.count() > 0:
            self.entry_list.setCurrentRow(0)
        else:
            self.new_entry()

        self._show_status(status_message, 3000)

    def _on_current_item_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return

        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.entry_list)
            self.entry_list.setCurrentItem(previous)
            del blocker
            return

        entry_id = current.data(Qt.ItemDataRole.UserRole)
        if self.current_entry is not None and self.current_entry.id == entry_id:
            return
        self._open_entry_by_id(entry_id, status_message="已重新打开该日记。")

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

    def _on_date_changed(self, *_args) -> None:
        self._refresh_footprint_relation()
        self._mark_dirty()

    def _refresh_footprint_relation(self) -> None:
        target_date = self.date_edit.date().toString("yyyy-MM-dd")
        count = len(self.footprint_storage.list_place_visits_by_date(target_date))
        self.footprint_hint_label.setText(f"当天足迹关联：{count} 条")
        self.show_footprints_button.setEnabled(count > 0)

    def _emit_show_footprints_requested(self) -> None:
        self.show_footprints_requested.emit(self.date_edit.date().toString("yyyy-MM-dd"))

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
            "当前日记有未保存内容，是否先保存？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_entry()
            return not self.is_dirty
        if reply == QMessageBox.StandardButton.Discard:
            return True
        return False

    def _refresh_image_list(self, select_row: int | None = 0) -> None:
        blocker = QSignalBlocker(self.image_list)
        self.image_list.clear()

        for index, image_item in enumerate(self.image_items, start=1):
            label = image_item.label.strip() or f"图片 {index}"
            if not self._is_current_entry_image(image_item.source_path):
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

    def _is_current_entry_image(self, image_path: Path) -> bool:
        if self.current_entry is None:
            return False
        return image_path.parent == self.storage.image_dir(self.current_entry.id)

    def _build_export_items(self, entries: list[DiaryEntry]) -> list[DiaryExportItem]:
        items: list[DiaryExportItem] = []
        for entry in entries:
            image_lookup = {
                image.file_name: self.storage.resolve_image_path(entry.id, image.file_name)
                for image in entry.images
            }
            items.append(DiaryExportItem(entry=entry, image_lookup=image_lookup))
        return items

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
