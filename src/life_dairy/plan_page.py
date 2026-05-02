from __future__ import annotations

from PySide6.QtCore import QDate, QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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
from .models import PlanItem
from .plan_storage import PLAN_TYPE_LABELS, PLAN_TYPE_VALUES, SUBTRACT_MODES, PlanStorage
from .ui_helpers import make_scroll_area


class PlanPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)

    def __init__(self, storage: PlanStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.storage = storage
        self.current_plan: PlanItem | None = None
        self.is_dirty = False
        self._is_loading_form = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_list()
        if self.plan_list.count() > 0:
            self.plan_list.setCurrentRow(0)
        else:
            self.new_plan()

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

        title = QLabel("轻计划", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 备注 / 减法字段 / 标签")
        self.search_input.textChanged.connect(self.refresh_list)

        self.type_filter_combo = QComboBox(widget)
        self.type_filter_combo.addItems(["全部", "加法计划", "减法计划"])
        self.type_filter_combo.currentTextChanged.connect(self.refresh_list)

        self.new_button = QPushButton("新建计划", widget)
        self.new_button.clicked.connect(self.new_plan)
        self.delete_button = QPushButton("删除当前计划", widget)
        self.delete_button.clicked.connect(self.delete_current_plan)

        self.plan_list = QListWidget(widget)
        self.plan_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.type_filter_combo)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.plan_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_plan)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_plan)
        self.done_button = QPushButton("标记完成", widget)
        self.done_button.clicked.connect(self.mark_done)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addWidget(self.done_button)
        action_row.addStretch(1)

        form = QFormLayout()
        self.plan_type_combo = QComboBox(widget)
        self.plan_type_combo.addItems(["加法计划", "减法计划"])
        self.plan_type_combo.currentTextChanged.connect(self._on_plan_type_changed)

        self.title_input = QLineEdit(widget)
        self.title_input.setPlaceholderText("例如：整理四月照片、周末读完两章")
        self.title_input.textChanged.connect(self._mark_dirty)

        self.due_date_edit = QDateEdit(widget)
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_date_edit.dateChanged.connect(self._mark_dirty)

        self.status_combo = QComboBox(widget)
        self.status_combo.addItems(["未开始", "进行中", "已完成", "搁置"])
        self.status_combo.currentTextChanged.connect(self._mark_dirty)

        self.priority_combo = QComboBox(widget)
        self.priority_combo.addItems(["低", "普通", "高"])
        self.priority_combo.currentTextChanged.connect(self._mark_dirty)

        self.tags_input = QLineEdit(widget)
        self.tags_input.setPlaceholderText("多个标签用逗号分隔")
        self.tags_input.textChanged.connect(self._mark_dirty)

        form.addRow("计划类型", self.plan_type_combo)
        form.addRow("计划", self.title_input)
        form.addRow("日期", self.due_date_edit)
        form.addRow("状态", self.status_combo)
        form.addRow("优先级", self.priority_combo)
        form.addRow("标签", self.tags_input)

        self.subtract_group = QGroupBox("减法计划", widget)
        subtract_layout = QFormLayout(self.subtract_group)
        self.subtract_mode_combo = QComboBox(self.subtract_group)
        self.subtract_mode_combo.addItems(SUBTRACT_MODES)
        self.subtract_mode_combo.currentTextChanged.connect(self._mark_dirty)

        self.trigger_scene_input = QLineEdit(self.subtract_group)
        self.trigger_scene_input.setPlaceholderText("例如：晚上回宿舍后感到疲惫")
        self.trigger_scene_input.textChanged.connect(self._mark_dirty)

        self.avoid_behavior_input = QLineEdit(self.subtract_group)
        self.avoid_behavior_input.setPlaceholderText("例如：连续刷短视频超过30分钟")
        self.avoid_behavior_input.textChanged.connect(self._mark_dirty)

        self.reason_edit = QTextEdit(self.subtract_group)
        self.reason_edit.setPlaceholderText("为什么要少做 / 不做这件事")
        self.reason_edit.setMinimumHeight(90)
        self.reason_edit.textChanged.connect(self._mark_dirty)

        self.alternative_action_edit = QTextEdit(self.subtract_group)
        self.alternative_action_edit.setPlaceholderText("触发时用什么行为替代")
        self.alternative_action_edit.setMinimumHeight(90)
        self.alternative_action_edit.textChanged.connect(self._mark_dirty)

        subtract_layout.addRow("减法类型", self.subtract_mode_combo)
        subtract_layout.addRow("触发场景", self.trigger_scene_input)
        subtract_layout.addRow("我想避免的行为", self.avoid_behavior_input)
        subtract_layout.addRow("为什么要避免", self.reason_edit)
        subtract_layout.addRow("替代行为", self.alternative_action_edit)

        notes_label = QLabel("备注", widget)
        self.notes_edit = QTextEdit(widget)
        self.notes_edit.setPlaceholderText("这里写轻量计划，不做复杂项目管理，只记录下一步。")
        self.notes_edit.setMinimumHeight(360)
        self.notes_edit.textChanged.connect(self._mark_dirty)

        layout.addLayout(action_row)
        layout.addLayout(form)
        layout.addWidget(self.subtract_group)
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_edit, 1)
        return widget

    def refresh_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id
        if current_id is None and self.current_plan is not None:
            current_id = self.current_plan.id

        blocker = QSignalBlocker(self.plan_list)
        self.plan_list.clear()
        target_row = -1
        for row, plan in enumerate(self.storage.list_plans(self.search_input.text(), self._current_filter_value())):
            item = QListWidgetItem(self._build_plan_list_text(plan))
            item.setData(Qt.ItemDataRole.UserRole, plan.id)
            item.setToolTip(plan.notes[:150] or plan.display_title)
            self.plan_list.addItem(item)
            if current_id and plan.id == current_id:
                target_row = row

        if target_row >= 0:
            self.plan_list.setCurrentRow(target_row)
        del blocker

    def new_plan(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_plan())
        self.plan_list.blockSignals(True)
        self.plan_list.clearSelection()
        self.plan_list.blockSignals(False)
        self._show_status("已创建新的轻计划草稿。", 3000)

    def save_plan(self) -> bool:
        plan = self._read_form()
        try:
            saved = self.storage.save_plan(plan)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存轻计划时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_list(select_id=saved.id)
        self._show_status("已保存轻计划到本地。", 3000)
        return True

    def reload_current_plan(self) -> None:
        if self.current_plan is None:
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
        if self.storage.plan_dir(self.current_plan.id).exists():
            try:
                plan = self.storage.load_plan(self.current_plan.id)
            except Exception as exc:
                QMessageBox.critical(self, "读取失败", f"恢复已保存内容时出错：\n{exc}")
                self._resume_auto_save()
                return
            self._fill_form(plan)
            self.refresh_list(select_id=plan.id)
            self._show_status("已恢复到上次保存的轻计划内容。", 3000)
        self._resume_auto_save()

    def delete_current_plan(self) -> None:
        if self.current_plan is None:
            return
        if not self.storage.plan_dir(self.current_plan.id).exists():
            reply = QMessageBox.question(
                self,
                "放弃草稿",
                "这个轻计划草稿还没有保存，确定要放弃吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._discard_current_draft("已放弃未保存的轻计划草稿。")
            return

        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定要删除这个轻计划吗？\n\n{self.current_plan.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_plan(self.current_plan.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除轻计划时出错：\n{exc}")
            return
        self.current_plan = None
        self._set_dirty(False)
        self.refresh_list()
        if self.plan_list.count() > 0:
            self.plan_list.setCurrentRow(0)
        else:
            self.new_plan()
        self._show_status("已删除当前轻计划。", 3000)

    def mark_done(self) -> None:
        self.status_combo.setCurrentText("已完成")
        self.save_plan()

    def _fill_form(self, plan: PlanItem) -> None:
        self._is_loading_form = True
        self.current_plan = plan
        try:
            self.title_input.setText(plan.title)
            self.plan_type_combo.setCurrentText(PLAN_TYPE_LABELS.get(plan.plan_type, "加法计划"))
            date_value = QDate.fromString(plan.due_date, "yyyy-MM-dd")
            self.due_date_edit.setDate(date_value if date_value.isValid() else QDate.currentDate())
            self.status_combo.setCurrentText(plan.status if plan.status in ["未开始", "进行中", "已完成", "搁置"] else "未开始")
            self.priority_combo.setCurrentText(plan.priority if plan.priority in ["低", "普通", "高"] else "普通")
            self.tags_input.setText(", ".join(plan.tags))
            self.subtract_mode_combo.setCurrentText(plan.subtract_mode if plan.subtract_mode in SUBTRACT_MODES else "少做")
            self.trigger_scene_input.setText(plan.trigger_scene)
            self.avoid_behavior_input.setText(plan.avoid_behavior)
            self.reason_edit.setPlainText(plan.reason)
            self.alternative_action_edit.setPlainText(plan.alternative_action)
            self.notes_edit.setPlainText(plan.notes)
            self._refresh_subtract_fields()
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> PlanItem:
        if self.current_plan is None:
            self.current_plan = self.storage.create_empty_plan()
        self.current_plan.title = self.title_input.text().strip()
        self.current_plan.due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        self.current_plan.status = self.status_combo.currentText().strip() or "未开始"
        self.current_plan.priority = self.priority_combo.currentText().strip() or "普通"
        self.current_plan.tags = [
            item.strip()
            for item in self.tags_input.text().replace("，", ",").split(",")
            if item.strip()
        ]
        self.current_plan.plan_type = PLAN_TYPE_VALUES.get(self.plan_type_combo.currentText(), "add")
        self.current_plan.subtract_mode = self.subtract_mode_combo.currentText().strip()
        self.current_plan.trigger_scene = self.trigger_scene_input.text().strip()
        self.current_plan.avoid_behavior = self.avoid_behavior_input.text().strip()
        self.current_plan.reason = self.reason_edit.toPlainText()
        self.current_plan.alternative_action = self.alternative_action_edit.toPlainText()
        self.current_plan.notes = self.notes_edit.toPlainText()
        return self.current_plan

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.plan_list)
            self.plan_list.setCurrentItem(previous)
            del blocker
            return
        plan_id = current.data(Qt.ItemDataRole.UserRole)
        if self.current_plan is not None and self.current_plan.id == plan_id:
            return
        try:
            plan = self.storage.load_plan(plan_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取轻计划时出错：\n{exc}")
            return
        self._fill_form(plan)
        self.refresh_list(select_id=plan.id)

    def open_plan_by_id(self, plan_id: str) -> None:
        try:
            plan = self.storage.load_plan(plan_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取轻计划时出错：\n{exc}")
            return
        self._fill_form(plan)
        self.refresh_list(select_id=plan.id)

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_plan = None
        self._set_dirty(False)
        self.refresh_list()
        if self.plan_list.count() > 0:
            self.plan_list.setCurrentRow(0)
        else:
            self.new_plan()
        self._show_status(status_message, 3000)

    def _build_plan_list_text(self, plan: PlanItem) -> str:
        prefix = "【减法】" if plan.plan_type == "subtract" else "【加法】"
        subtitle_parts = [plan.due_date, plan.status, plan.priority]
        if plan.plan_type == "subtract" and plan.subtract_mode:
            subtitle_parts.append(plan.subtract_mode)
        return f"{prefix}{plan.display_title}\n{' | '.join(subtitle_parts)}"

    def _current_filter_value(self) -> str:
        if not hasattr(self, "type_filter_combo"):
            return "all"
        return {
            "加法计划": "add",
            "减法计划": "subtract",
        }.get(self.type_filter_combo.currentText(), "all")

    def _on_plan_type_changed(self, *_args) -> None:
        self._refresh_subtract_fields()
        self._mark_dirty()

    def _refresh_subtract_fields(self) -> None:
        if not hasattr(self, "subtract_group"):
            return
        self.subtract_group.setVisible(self.plan_type_combo.currentText() == "减法计划")

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
        return self.save_plan()

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_plan is None:
            return False
        if self.storage.plan_dir(self.current_plan.id).exists():
            return True
        return bool(
            self.title_input.text().strip()
            or self.notes_edit.toPlainText().strip()
            or self.tags_input.text().strip()
            or self.trigger_scene_input.text().strip()
            or self.avoid_behavior_input.text().strip()
            or self.reason_edit.toPlainText().strip()
            or self.alternative_action_edit.toPlainText().strip()
        )

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
