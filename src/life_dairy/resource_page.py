from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
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
from .lesson_storage import LessonStorage
from .plan_storage import PlanStorage
from .resource_storage import (
    MONEY_CYCLES,
    MONEY_DIRECTIONS,
    RESOURCE_ITEM_TYPES,
    RESOURCE_STATUSES,
    RESOURCE_TYPES,
    TIME_BLOCK_OPTIONS,
    ResourceEntry,
    ResourceStorage,
)
from .ui_helpers import make_scroll_area


class ResourcePage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)
    plan_created = Signal(str)
    lesson_created = Signal(str)

    def __init__(
        self,
        storage: ResourceStorage,
        plan_storage: PlanStorage,
        lesson_storage: LessonStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.plan_storage = plan_storage
        self.lesson_storage = lesson_storage
        self.current_resource: ResourceEntry | None = None
        self.is_dirty = False
        self._is_loading_form = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_resource_list()
        if self.resource_list.count() > 0 and self.resource_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.resource_list.setCurrentRow(0)
        else:
            self.new_resource()

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
        splitter.setSizes([310, 900])
        layout.addWidget(make_scroll_area(splitter))

    def _build_sidebar(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("轻资源", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 资源项 / 判断 / 备注")
        self.search_input.textChanged.connect(self.refresh_resource_list)
        self.type_filter_combo = QComboBox(widget)
        self.type_filter_combo.addItems(["全部", *RESOURCE_TYPES])
        self.type_filter_combo.currentTextChanged.connect(self.refresh_resource_list)
        self.status_filter_combo = QComboBox(widget)
        self.status_filter_combo.addItems(["全部", *RESOURCE_STATUSES])
        self.status_filter_combo.currentTextChanged.connect(self.refresh_resource_list)
        self.new_button = QPushButton("新建轻资源", widget)
        self.new_button.clicked.connect(self.new_resource)
        self.delete_button = QPushButton("删除当前记录", widget)
        self.delete_button.clicked.connect(self.delete_current_resource)
        self.resource_list = QListWidget(widget)
        self.resource_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.type_filter_combo)
        layout.addWidget(self.status_filter_combo)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.resource_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_resource)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_resource)
        self.to_plan_button = QPushButton("转成轻计划", widget)
        self.to_plan_button.clicked.connect(self.convert_to_plan)
        self.to_lesson_button = QPushButton("复制为教训反思", widget)
        self.to_lesson_button.clicked.connect(self.copy_to_lesson)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addWidget(self.to_plan_button)
        action_row.addWidget(self.to_lesson_button)
        action_row.addStretch(1)

        info_group = QGroupBox("资源判断", widget)
        info_layout = QVBoxLayout(info_group)
        form = QFormLayout()
        self.title_input = QLineEdit(info_group)
        self.title_input.setPlaceholderText("这件事是什么")
        self.title_input.textChanged.connect(self._mark_dirty)
        self.type_combo = QComboBox(info_group)
        self.type_combo.addItems(RESOURCE_TYPES)
        self.type_combo.currentTextChanged.connect(self._mark_dirty)
        self.status_combo = QComboBox(info_group)
        self.status_combo.addItems(RESOURCE_STATUSES)
        self.status_combo.currentTextChanged.connect(self._mark_dirty)
        form.addRow("标题", self.title_input)
        form.addRow("类型", self.type_combo)
        form.addRow("状态", self.status_combo)
        info_layout.addLayout(form)
        self.description_edit = self._make_text_edit("描述：这件事大概是什么。")
        self.judgement_edit = self._make_text_edit("总体判断：值不值得？哪里贵？")
        self.feeling_edit = self._make_text_edit("主观感受：身体和情绪怎么反应？")
        self.notes_edit = self._make_text_edit("备注")
        info_layout.addWidget(QLabel("描述", info_group))
        info_layout.addWidget(self.description_edit)
        info_layout.addWidget(QLabel("总体判断", info_group))
        info_layout.addWidget(self.judgement_edit)
        info_layout.addWidget(QLabel("主观感受", info_group))
        info_layout.addWidget(self.feeling_edit)
        info_layout.addWidget(QLabel("备注", info_group))
        info_layout.addWidget(self.notes_edit)

        item_group = self._build_item_group(widget)
        recurrence_group = QGroupBox("轮回测试", widget)
        recurrence_layout = QVBoxLayout(recurrence_group)
        self.next_week_edit = self._make_text_edit("如果这件事下周再来一次，我还愿意做吗？")
        self.one_year_edit = self._make_text_edit("如果这种模式持续一年，我会变成什么样？")
        self.repeat_edit = self._make_text_edit("我是否愿意主动重复它？")
        recurrence_layout.addWidget(QLabel("如果这件事下周再来一次，我还愿意做吗？", recurrence_group))
        recurrence_layout.addWidget(self.next_week_edit)
        recurrence_layout.addWidget(QLabel("如果这种模式持续一年，我会变成什么样？", recurrence_group))
        recurrence_layout.addWidget(self.one_year_edit)
        recurrence_layout.addWidget(QLabel("我是否愿意主动重复它？", recurrence_group))
        recurrence_layout.addWidget(self.repeat_edit)

        lower_splitter = QSplitter(Qt.Orientation.Horizontal, widget)
        lower_splitter.addWidget(item_group)
        lower_splitter.addWidget(recurrence_group)
        lower_splitter.setSizes([520, 460])

        layout.addLayout(action_row)
        layout.addWidget(info_group, 2)
        layout.addWidget(lower_splitter, 1)
        return widget

    def _build_item_group(self, parent: QWidget) -> QWidget:
        group = QGroupBox("资源项", parent)
        layout = QHBoxLayout(group)
        left = QVBoxLayout()
        self.item_list = QListWidget(group)
        self.item_list.currentItemChanged.connect(self._load_selected_item_to_editor)
        item_buttons = QHBoxLayout()
        self.add_item_button = QPushButton("添加资源项", group)
        self.add_item_button.clicked.connect(self.add_resource_item)
        self.update_item_button = QPushButton("更新所选", group)
        self.update_item_button.clicked.connect(self.update_selected_resource_item)
        self.remove_item_button = QPushButton("删除资源项", group)
        self.remove_item_button.clicked.connect(self.remove_selected_resource_item)
        item_buttons.addWidget(self.add_item_button)
        item_buttons.addWidget(self.update_item_button)
        item_buttons.addWidget(self.remove_item_button)
        left.addWidget(self.item_list, 1)
        left.addLayout(item_buttons)

        form = QFormLayout()
        self.item_type_combo = QComboBox(group)
        self.item_type_combo.addItems(RESOURCE_ITEM_TYPES)
        self.item_direct_time_input = QLineEdit(group)
        self.item_indirect_time_input = QLineEdit(group)
        self.item_recovery_time_input = QLineEdit(group)
        self.item_block_combo = QComboBox(group)
        self.item_block_combo.addItems(TIME_BLOCK_OPTIONS)
        self.item_money_amount = QDoubleSpinBox(group)
        self.item_money_amount.setRange(-100000000, 100000000)
        self.item_money_amount.setDecimals(2)
        self.item_money_cycle = QComboBox(group)
        self.item_money_cycle.addItems(MONEY_CYCLES)
        self.item_money_direction = QComboBox(group)
        self.item_money_direction.addItems(MONEY_DIRECTIONS)
        self.item_value_input = QLineEdit(group)
        self.item_note_input = QTextEdit(group)
        self.item_note_input.setMinimumHeight(80)
        form.addRow("资源类型", self.item_type_combo)
        form.addRow("直接时间", self.item_direct_time_input)
        form.addRow("间接时间", self.item_indirect_time_input)
        form.addRow("恢复时间", self.item_recovery_time_input)
        form.addRow("是否打断整块时间", self.item_block_combo)
        form.addRow("金额", self.item_money_amount)
        form.addRow("周期", self.item_money_cycle)
        form.addRow("收入 / 支出 / 预留", self.item_money_direction)
        form.addRow("其他数量或描述", self.item_value_input)
        form.addRow("备注", self.item_note_input)

        layout.addLayout(left, 1)
        layout.addLayout(form, 1)
        return group

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit(self)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(78)
        edit.textChanged.connect(self._mark_dirty)
        return edit

    def refresh_resource_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id or (self.current_resource.id if self.current_resource is not None else None)
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        resource_type = self.type_filter_combo.currentText() if hasattr(self, "type_filter_combo") else "全部"
        status = self.status_filter_combo.currentText() if hasattr(self, "status_filter_combo") else "全部"
        blocker = QSignalBlocker(self.resource_list)
        self.resource_list.clear()
        target_row = -1
        for row, resource in enumerate(self.storage.list_resources(query, resource_type, status)):
            item = QListWidgetItem(self._build_list_text(resource))
            item.setData(Qt.ItemDataRole.UserRole, resource.id)
            item.setToolTip(resource.overall_judgement or resource.description or resource.display_title)
            self.resource_list.addItem(item)
            if current_id and resource.id == current_id:
                target_row = row
        if target_row >= 0:
            self.resource_list.setCurrentRow(target_row)
        del blocker
        if self.resource_list.count() == 0:
            self.resource_list.addItem("暂无轻资源记录。")

    def new_resource(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_resource())
        self.resource_list.blockSignals(True)
        self.resource_list.clearSelection()
        self.resource_list.blockSignals(False)
        self._show_status("已创建新的轻资源草稿。", 3000)

    def save_resource(self) -> bool:
        resource = self._read_form()
        try:
            saved = self.storage.save_resource(resource)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存轻资源时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_resource_list(select_id=saved.id)
        self._show_status("轻资源已保存。", 3000)
        return True

    def reload_current_resource(self) -> None:
        if self.current_resource is None or not self.storage.resource_dir(self.current_resource.id).exists():
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
            resource = self.storage.load_resource(self.current_resource.id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取轻资源时出错：\n{exc}")
            return
        self._fill_form(resource)
        self.refresh_resource_list(select_id=resource.id)

    def delete_current_resource(self) -> None:
        if self.current_resource is None:
            return
        if not self.storage.resource_dir(self.current_resource.id).exists():
            reply = QMessageBox.question(self, "放弃草稿", "这条轻资源还没保存，确定放弃吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self._discard_current_draft("已放弃未保存的轻资源草稿。")
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定删除这条轻资源吗？\n\n{self.current_resource.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_resource(self.current_resource.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除轻资源时出错：\n{exc}")
            return
        self._discard_current_draft("已删除当前轻资源。")

    def add_resource_item(self) -> None:
        if self.current_resource is None:
            self.current_resource = self.storage.create_empty_resource()
        item = self._read_resource_item_form()
        self.current_resource.resource_items.append(item)
        self._refresh_item_list(select_row=len(self.current_resource.resource_items) - 1)
        self._mark_dirty()

    def update_selected_resource_item(self) -> None:
        if self.current_resource is None:
            return
        row = self.item_list.currentRow()
        if row < 0 or row >= len(self.current_resource.resource_items):
            return
        self.current_resource.resource_items[row] = self._read_resource_item_form()
        self._refresh_item_list(select_row=row)
        self._mark_dirty()

    def remove_selected_resource_item(self) -> None:
        if self.current_resource is None:
            return
        row = self.item_list.currentRow()
        if row < 0 or row >= len(self.current_resource.resource_items):
            return
        del self.current_resource.resource_items[row]
        self._refresh_item_list(select_row=min(row, len(self.current_resource.resource_items) - 1))
        self._mark_dirty()

    def convert_to_plan(self) -> None:
        if self.current_resource is None:
            return
        resource = self._read_form()
        plan = self.plan_storage.create_empty_plan()
        plan.title = resource.display_title
        plan.notes = self._resource_summary(resource)
        saved = self.plan_storage.save_plan(plan)
        resource.status = "已决定"
        self.storage.save_resource(resource)
        self.plan_created.emit(saved.id)
        self._show_status("已把轻资源转成轻计划。", 4000)

    def copy_to_lesson(self) -> None:
        if self.current_resource is None:
            return
        resource = self._read_form()
        lesson = self.lesson_storage.create_empty_lesson()
        lesson.title = resource.display_title
        lesson.category = "其他"
        lesson.event = resource.description
        lesson.cost = self._resource_summary(resource)
        lesson.next_action = resource.overall_judgement
        lesson.one_sentence = resource.subjective_feeling
        saved = self.lesson_storage.save_lesson(lesson)
        self.lesson_created.emit(saved.id)
        self._show_status("已复制为教训反思草稿。", 4000)

    def open_resource_by_id(self, resource_id: str, status_message: str | None = None) -> None:
        try:
            resource = self.storage.load_resource(resource_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取轻资源时出错：\n{exc}")
            return
        self._fill_form(resource)
        self.refresh_resource_list(select_id=resource.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _fill_form(self, resource: ResourceEntry) -> None:
        self._is_loading_form = True
        self.current_resource = resource
        try:
            self.title_input.setText(resource.title)
            self._set_combo_text(self.type_combo, resource.resource_type)
            self._set_combo_text(self.status_combo, resource.status)
            self.description_edit.setPlainText(resource.description)
            self.judgement_edit.setPlainText(resource.overall_judgement)
            self.feeling_edit.setPlainText(resource.subjective_feeling)
            self.notes_edit.setPlainText(resource.notes)
            recurrence = resource.recurrence_test or {}
            self.next_week_edit.setPlainText(str(recurrence.get("next_week", "")))
            self.one_year_edit.setPlainText(str(recurrence.get("one_year", "")))
            self.repeat_edit.setPlainText(str(recurrence.get("repeat_willingness", "")))
            self._refresh_item_list()
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> ResourceEntry:
        if self.current_resource is None:
            self.current_resource = self.storage.create_empty_resource()
        self.current_resource.title = self.title_input.text().strip()
        self.current_resource.resource_type = self.type_combo.currentText().strip() or "其他"
        self.current_resource.status = self.status_combo.currentText().strip() or "考虑中"
        self.current_resource.description = self.description_edit.toPlainText()
        self.current_resource.overall_judgement = self.judgement_edit.toPlainText()
        self.current_resource.subjective_feeling = self.feeling_edit.toPlainText()
        self.current_resource.notes = self.notes_edit.toPlainText()
        self.current_resource.recurrence_test = {
            "next_week": self.next_week_edit.toPlainText(),
            "one_year": self.one_year_edit.toPlainText(),
            "repeat_willingness": self.repeat_edit.toPlainText(),
        }
        return self.current_resource

    def _read_resource_item_form(self) -> dict:
        item_type = self.item_type_combo.currentText().strip() or "其他"
        item = {
            "type": item_type,
            "value": self.item_value_input.text().strip(),
            "notes": self.item_note_input.toPlainText().strip(),
        }
        if item_type == "时间":
            item.update(
                {
                    "direct_time": self.item_direct_time_input.text().strip(),
                    "indirect_time": self.item_indirect_time_input.text().strip(),
                    "recovery_time": self.item_recovery_time_input.text().strip(),
                    "time_block_interrupt": self.item_block_combo.currentText(),
                }
            )
        if item_type == "金钱":
            item.update(
                {
                    "amount": self.item_money_amount.value(),
                    "cycle": self.item_money_cycle.currentText(),
                    "direction": self.item_money_direction.currentText(),
                }
            )
        return item

    def _load_selected_item_to_editor(self, *_args) -> None:
        if self.current_resource is None:
            return
        row = self.item_list.currentRow()
        if row < 0 or row >= len(self.current_resource.resource_items):
            return
        item = self.current_resource.resource_items[row]
        self._set_combo_text(self.item_type_combo, str(item.get("type", "其他")))
        self.item_direct_time_input.setText(str(item.get("direct_time", "")))
        self.item_indirect_time_input.setText(str(item.get("indirect_time", "")))
        self.item_recovery_time_input.setText(str(item.get("recovery_time", "")))
        self._set_combo_text(self.item_block_combo, str(item.get("time_block_interrupt", "不打断")))
        try:
            self.item_money_amount.setValue(float(item.get("amount", 0) or 0))
        except (TypeError, ValueError):
            self.item_money_amount.setValue(0)
        self._set_combo_text(self.item_money_cycle, str(item.get("cycle", "一次性")))
        self._set_combo_text(self.item_money_direction, str(item.get("direction", "支出")))
        self.item_value_input.setText(str(item.get("value", "")))
        self.item_note_input.setPlainText(str(item.get("notes", "")))

    def _refresh_item_list(self, select_row: int | None = 0) -> None:
        blocker = QSignalBlocker(self.item_list)
        self.item_list.clear()
        for item in self.current_resource.resource_items if self.current_resource else []:
            self.item_list.addItem(self._describe_item(item))
        if select_row is not None and 0 <= select_row < self.item_list.count():
            self.item_list.setCurrentRow(select_row)
        del blocker
        self._load_selected_item_to_editor()

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        resource_id = current.data(Qt.ItemDataRole.UserRole)
        if not resource_id:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.resource_list)
            self.resource_list.setCurrentItem(previous)
            del blocker
            return
        if self.current_resource is not None and self.current_resource.id == resource_id:
            return
        self.open_resource_by_id(resource_id, status_message="已打开这条轻资源。")

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_resource = None
        self._set_dirty(False)
        self.refresh_resource_list()
        if self.resource_list.count() > 0 and self.resource_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.resource_list.setCurrentRow(0)
        else:
            self.new_resource()
        self._show_status(status_message, 3000)

    def _describe_item(self, item: dict) -> str:
        item_type = str(item.get("type", "其他"))
        if item_type == "时间":
            parts = [item.get("direct_time", ""), item.get("indirect_time", ""), item.get("recovery_time", "")]
            return f"时间 | {' / '.join(str(part) for part in parts if part)} | {item.get('time_block_interrupt', '')}"
        if item_type == "金钱":
            return f"金钱 | {item.get('amount', 0)} | {item.get('cycle', '')} | {item.get('direction', '')}"
        return f"{item_type} | {item.get('value', '') or item.get('notes', '')}"

    def _resource_summary(self, resource: ResourceEntry) -> str:
        items = "\n".join(f"- {self._describe_item(item)}" for item in resource.resource_items)
        recurrence = resource.recurrence_test or {}
        return "\n\n".join(
            part
            for part in [
                f"来源轻资源：{resource.id}",
                resource.description,
                f"资源项：\n{items}" if items else "",
                f"总体判断：{resource.overall_judgement}" if resource.overall_judgement else "",
                f"主观感受：{resource.subjective_feeling}" if resource.subjective_feeling else "",
                "轮回测试：\n"
                f"下周再来：{recurrence.get('next_week', '')}\n"
                f"持续一年：{recurrence.get('one_year', '')}\n"
                f"主动重复：{recurrence.get('repeat_willingness', '')}",
                resource.notes,
            ]
            if part.strip()
        )

    def _build_list_text(self, resource: ResourceEntry) -> str:
        return f"{resource.display_title}\n{resource.resource_type} | {resource.status}"

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
        resource = self._read_form()
        try:
            self.storage.save_resource(resource)
        except Exception:
            return False
        self._set_dirty(False)
        return True

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_resource is None:
            return False
        if self.storage.resource_dir(self.current_resource.id).exists():
            return True
        return bool(
            self.title_input.text().strip()
            or self.description_edit.toPlainText().strip()
            or self.judgement_edit.toPlainText().strip()
            or self.feeling_edit.toPlainText().strip()
            or self.notes_edit.toPlainText().strip()
            or self.current_resource.resource_items
        )

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
