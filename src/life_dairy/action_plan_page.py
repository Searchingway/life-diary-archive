from __future__ import annotations

from datetime import date as dt_date
from pathlib import Path
from uuid import uuid4 as _uuid4

from PySide6.QtCore import QDate, QRectF, QSignalBlocker, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .action_plan_storage import (
    ACTION_PLAN_STATUSES,
    ACTION_PLAN_TYPES,
    ActionPlanItem,
    ActionPlanStorage,
    ActionPlanTask,
)
from .autosave import AutoSaveMixin
from .ui_helpers import make_scroll_area

_TASK_RADIUS = 28.0
_CHAIN_SPACING = 180.0
_NODE_V_SPACING = 80.0
_SCENE_MARGIN = 60.0


class _PlanEditDialog(QDialog):
    def __init__(self, plan: ActionPlanItem, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("编辑行动计划" if plan.title else "新建行动计划")
        self.setMinimumWidth(480)
        self._plan = plan
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("计划标题")
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(ACTION_PLAN_TYPES)
        self.desc_edit = QTextEdit(self)
        self.desc_edit.setPlaceholderText("目标描述")
        self.desc_edit.setMinimumHeight(70)
        self.start_date = QDateEdit(QDate.currentDate(), self)
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date = QDateEdit(QDate.currentDate().addDays(7), self)
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.daily_time = QLineEdit(self)
        self.daily_time.setPlaceholderText("例如: 1小时")
        self.priority_combo = QComboBox(self)
        self.priority_combo.addItems(["低", "普通", "高"])
        self.status_combo = QComboBox(self)
        self.status_combo.addItems(ACTION_PLAN_STATUSES)
        self.summary_edit = QTextEdit(self)
        self.summary_edit.setPlaceholderText("完成总结（可选）")
        self.summary_edit.setMinimumHeight(60)

        form.addRow("标题", self.title_edit)
        form.addRow("类型", self.type_combo)
        form.addRow("描述", self.desc_edit)
        form.addRow("开始日期", self.start_date)
        form.addRow("截止日期", self.end_date)
        form.addRow("每日可用时间", self.daily_time)
        form.addRow("优先级", self.priority_combo)
        form.addRow("状态", self.status_combo)
        form.addRow("完成总结", self.summary_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        self.title_edit.setText(self._plan.title)
        self._set_combo(self.type_combo, self._plan.plan_type)
        self.desc_edit.setPlainText(self._plan.description)
        sd = QDate.fromString(self._plan.start_date, "yyyy-MM-dd")
        self.start_date.setDate(sd if sd.isValid() else QDate.currentDate())
        ed = QDate.fromString(self._plan.end_date, "yyyy-MM-dd")
        self.end_date.setDate(ed if ed.isValid() else QDate.currentDate().addDays(7))
        self.daily_time.setText(self._plan.daily_available_time)
        self._set_combo(self.priority_combo, self._plan.priority)
        self._set_combo(self.status_combo, self._plan.status)
        self.summary_edit.setPlainText(self._plan.summary)

    def apply_to(self, plan: ActionPlanItem) -> None:
        plan.title = self.title_edit.text().strip()
        plan.plan_type = self.type_combo.currentText()
        plan.description = self.desc_edit.toPlainText()
        plan.start_date = self.start_date.date().toString("yyyy-MM-dd")
        plan.end_date = self.end_date.date().toString("yyyy-MM-dd")
        plan.daily_available_time = self.daily_time.text().strip()
        plan.priority = self.priority_combo.currentText()
        plan.status = self.status_combo.currentText()
        plan.summary = self.summary_edit.toPlainText()

    @staticmethod
    def _set_combo(cb: QComboBox, text: str) -> None:
        idx = cb.findText(text)
        cb.setCurrentIndex(idx if idx >= 0 else 0)


class _TaskEditDialog(QDialog):
    def __init__(self, task: ActionPlanTask | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if task and task.title else "添加任务")
        self.setMinimumWidth(420)
        self._task = task or ActionPlanTask(id=_uuid4().hex, title="", date=dt_date.today().isoformat())
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("任务标题")
        self.date_edit = QDateEdit(QDate.currentDate(), self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.minutes_combo = QComboBox(self)
        self.minutes_combo.addItems(["15", "30", "45", "60", "90", "120", "180"])
        self.minutes_combo.setCurrentText("30")
        self.note_edit = QLineEdit(self)
        self.note_edit.setPlaceholderText("备注（可选）")
        self.done_check = QCheckBox("已完成", self)

        form.addRow("标题", self.title_edit)
        form.addRow("日期", self.date_edit)
        form.addRow("预计耗时", self.minutes_combo)
        form.addRow("备注", self.note_edit)
        form.addRow("", self.done_check)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self) -> None:
        self.title_edit.setText(self._task.title)
        if self._task.date:
            d = QDate.fromString(self._task.date, "yyyy-MM-dd")
            self.date_edit.setDate(d if d.isValid() else QDate.currentDate())
        self.minutes_combo.setCurrentText(str(self._task.estimated_minutes) if self._task.estimated_minutes else "30")
        self.note_edit.setText(self._task.note)
        self.done_check.setChecked(self._task.done)

    @property
    def result(self) -> ActionPlanTask:
        self._task.title = self.title_edit.text().strip()
        self._task.date = self.date_edit.date().toString("yyyy-MM-dd")
        self._task.estimated_minutes = int(self.minutes_combo.currentText())
        self._task.note = self.note_edit.text().strip()
        self._task.done = self.done_check.isChecked()
        return self._task


class _TimelineWidget(QWidget):
    """Date-grouped task cards."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        from PySide6.QtWidgets import QScrollArea as _QSA
        self._scroll = _QSA(self)
        self._scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setSpacing(10)
        self._container_layout.addStretch(1)
        self._scroll.setWidget(self._container)
        layout.addWidget(self._scroll)

    def load_tasks(self, tasks: list[ActionPlanTask], on_toggle, on_edit_task) -> None:
        while self._container_layout.count() > 1:
            item = self._container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not tasks:
            empty = QLabel("暂无任务", self._container)
            empty.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._container_layout.insertWidget(0, empty)
            return

        groups: dict[str, list[ActionPlanTask]] = {}
        for t in sorted(tasks, key=lambda x: (x.date, x.title)):
            groups.setdefault(t.date, []).append(t)

        for date_str in sorted(groups.keys()):
            group = QGroupBox(date_str, self._container)
            group_layout = QVBoxLayout(group)
            group_layout.setSpacing(4)

            for task in groups[date_str]:
                row = QWidget(group)
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(4, 2, 4, 2)

                cb = QCheckBox(task.title, row)
                cb.setChecked(task.done)
                if task.done:
                    cb.setStyleSheet("text-decoration: line-through; color: #999;")
                cb.toggled.connect(lambda checked, t=task: on_toggle(t, checked))

                info = f"{task.estimated_minutes}分钟"
                if task.note:
                    info += f"  — {task.note}"
                lbl = QLabel(info, row)
                lbl.setStyleSheet("color: #888; font-size: 12px;")

                edit_btn = QPushButton("编辑", row)
                edit_btn.setFixedWidth(50)
                edit_btn.clicked.connect(lambda checked=None, t=task: on_edit_task(t))

                row_layout.addWidget(cb, 1)
                row_layout.addWidget(lbl)
                row_layout.addWidget(edit_btn)
                group_layout.addWidget(row)

            self._container_layout.insertWidget(
                self._container_layout.count() - 1, group
            )


class _TaskChainView(QGraphicsView):
    """Black-background node chain view."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setBackgroundBrush(QBrush(QColor(22, 24, 28)))
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._task_items: dict[str, QGraphicsEllipseItem] = {}
        self._on_toggle = None
        self._on_edit_task = None

    def load_tasks(
        self,
        tasks: list[ActionPlanTask],
        on_toggle,
        on_edit_task,
    ) -> None:
        self._scene.clear()
        self._task_items.clear()
        self._on_toggle = on_toggle
        self._on_edit_task = on_edit_task

        if not tasks:
            text = self._scene.addText("暂无任务")
            text.setDefaultTextColor(QColor(140, 140, 140))
            text.setFont(QFont("Microsoft YaHei", 14))
            text.setPos(_SCENE_MARGIN, _SCENE_MARGIN)
            return

        groups: dict[str, list[ActionPlanTask]] = {}
        for t in sorted(tasks, key=lambda x: (x.date, x.title)):
            groups.setdefault(t.date, []).append(t)

        sorted_dates = sorted(groups.keys())
        chain_pen = QPen(QColor(70, 72, 78), 2)

        for chain_idx, date_str in enumerate(sorted_dates):
            day_tasks = groups[date_str]
            cx = _SCENE_MARGIN + chain_idx * _CHAIN_SPACING

            date_text = self._scene.addText(date_str)
            date_text.setDefaultTextColor(QColor(180, 184, 190))
            date_text.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
            date_text.setPos(cx - 28, _SCENE_MARGIN - 10)

            start_y = _SCENE_MARGIN + 40
            for ti, task in enumerate(day_tasks):
                node_y = start_y + ti * _NODE_V_SPACING

                if task.x is not None and task.y is not None:
                    cx_pos = task.x
                    node_y_pos = task.y
                else:
                    cx_pos = cx
                    node_y_pos = node_y

                if ti > 0:
                    prev_y = start_y + (ti - 1) * _NODE_V_SPACING
                    line = self._scene.addLine(cx_pos, prev_y + _TASK_RADIUS, cx_pos, node_y_pos - _TASK_RADIUS, chain_pen)
                    line.setZValue(-1)

                node = _TaskNode(task, cx_pos, node_y_pos, _TASK_RADIUS)
                node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
                node.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
                node.setAcceptHoverEvents(True)
                self._scene.addItem(node)
                self._task_items[task.id] = node

        total_w = len(sorted_dates) * _CHAIN_SPACING + _SCENE_MARGIN
        total_h = max(
            _SCENE_MARGIN + 60 + max(len(groups[d]) for d in sorted_dates) * _NODE_V_SPACING,
            300,
        )
        self._scene.setSceneRect(0, 0, total_w, total_h)

    def mouseDoubleClickEvent(self, event) -> None:
        item = self.itemAt(event.position().toPoint())
        if isinstance(item, _TaskNode) and self._on_edit_task:
            self._on_edit_task(item.task)
        super().mouseDoubleClickEvent(event)

    def collect_positions(self) -> dict[str, tuple[float, float]]:
        result: dict[str, tuple[float, float]] = {}
        for task_id, item in self._task_items.items():
            if isinstance(item, _TaskNode):
                result[task_id] = (item.scenePos().x(), item.scenePos().y())
        return result


class _TaskNode(QGraphicsEllipseItem):
    def __init__(self, task: ActionPlanTask, cx: float, cy: float, radius: float):
        super().__init__(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
        self.task = task
        self._radius = radius
        self._update_style()
        self.setZValue(1)

        label = QGraphicsTextItem(task.title[:8] + (".." if len(task.title) > 8 else ""), self)
        label.setDefaultTextColor(QColor(240, 240, 240))
        label.setFont(QFont("Microsoft YaHei", 8))
        label_rect = label.boundingRect()
        label.setPos(cx - label_rect.width() / 2 + radius - cx + cx, cy - label_rect.height() / 2 - cy + cy)

        self.setToolTip(
            f"{task.title}\n日期: {task.date}\n预计: {task.estimated_minutes}分钟\n"
            f"状态: {'已完成' if task.done else '未完成'}\n{task.note or ''}"
        )

    def _update_style(self) -> None:
        if self.task.done:
            brush = QBrush(QColor(60, 180, 120))
            pen = QPen(QColor(80, 220, 140), 3)
        else:
            gradient = QLinearGradient(0, 0, 0, self._radius * 2)
            gradient.setColorAt(0, QColor(90, 140, 220))
            gradient.setColorAt(1, QColor(40, 80, 160))
            brush = QBrush(gradient)
            pen = QPen(QColor(120, 160, 230), 2)
        self.setBrush(brush)
        self.setPen(pen)


class ActionPlanPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)
    action_plan_created = Signal(str)

    def __init__(self, storage: ActionPlanStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.storage = storage
        self.current_plan: ActionPlanItem | None = None
        self.is_dirty = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_list()
        if self.plan_list.count() > 0:
            self.plan_list.setCurrentRow(0)
        else:
            self._show_empty_state()

    def has_unsaved_changes(self) -> bool:
        return self.is_dirty

    def maybe_finish_pending_changes(self) -> bool:
        return AutoSaveMixin.maybe_finish_pending_changes(self)

    # --- UI ---

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_main())
        splitter.setSizes([280, 980])
        layout.addWidget(splitter)

    def _build_sidebar(self) -> QWidget:
        w = QWidget(self)
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(8)
        title = QLabel("行动计划", w)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(w)
        self.search_input.setPlaceholderText("搜索标题 / 描述 / 任务")
        self.search_input.textChanged.connect(self.refresh_list)
        self.status_filter = QComboBox(w)
        self.status_filter.addItems(["全部", *ACTION_PLAN_STATUSES])
        self.status_filter.currentTextChanged.connect(self.refresh_list)
        self.new_btn = QPushButton("新建行动计划", w)
        self.new_btn.clicked.connect(self.new_plan)
        self.delete_btn = QPushButton("删除当前计划", w)
        self.delete_btn.clicked.connect(self.delete_current_plan)
        self.plan_list = QListWidget(w)
        self.plan_list.currentItemChanged.connect(self._on_select)
        lo.addWidget(title)
        lo.addWidget(self.search_input)
        lo.addWidget(self.status_filter)
        lo.addWidget(self.new_btn)
        lo.addWidget(self.delete_btn)
        lo.addWidget(self.plan_list, 1)
        return w

    def _build_main(self) -> QWidget:
        w = QWidget(self)
        lo = QVBoxLayout(w)
        lo.setContentsMargins(12, 0, 0, 0)
        lo.setSpacing(8)

        self._build_header(lo)

        self._mode_tabs = QTabWidget(w)
        self._timeline = _TimelineWidget(w)
        self._chain_view = None
        self._chain_placeholder = QLabel("任务链模式需要图形加速支持，当前环境不可用。", w)
        self._chain_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._chain_placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 60px;")
        self._mode_tabs.addTab(self._timeline, "时间表")
        self._mode_tabs.addTab(self._chain_placeholder, "任务链")
        self._mode_tabs.currentChanged.connect(self._on_mode_changed)
        lo.addWidget(self._mode_tabs, 1)

        task_bar = QHBoxLayout()
        self.add_task_btn = QPushButton("添加任务", w)
        self.add_task_btn.clicked.connect(self._add_task)
        self.edit_task_btn = QPushButton("编辑所选任务", w)
        self.edit_task_btn.clicked.connect(self._edit_selected_task)
        self.delete_task_btn = QPushButton("删除所选任务", w)
        self.delete_task_btn.clicked.connect(self._delete_selected_task)
        task_bar.addWidget(self.add_task_btn)
        task_bar.addWidget(self.edit_task_btn)
        task_bar.addWidget(self.delete_task_btn)
        task_bar.addStretch(1)
        lo.addLayout(task_bar)

        return w

    def _build_header(self, parent_layout: QVBoxLayout) -> None:
        self.header_widget = QWidget(self)
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(0, 0, 0, 6)

        info = QVBoxLayout()
        self.plan_title_label = QLabel("选择一个行动计划", self.header_widget)
        self.plan_title_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.plan_meta_label = QLabel("", self.header_widget)
        self.plan_meta_label.setStyleSheet("color: #666; font-size: 12px;")
        self.progress_bar = QProgressBar(self.header_widget)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setFormat("进度: %p%")
        info.addWidget(self.plan_title_label)
        info.addWidget(self.plan_meta_label)
        info.addWidget(self.progress_bar)

        btns = QVBoxLayout()
        self.edit_plan_btn = QPushButton("编辑计划", self.header_widget)
        self.edit_plan_btn.clicked.connect(self._edit_plan)
        self.ai_decompose_btn = QPushButton("AI 拆解", self.header_widget)
        self.ai_decompose_btn.clicked.connect(self._ai_decompose)
        btns.addWidget(self.edit_plan_btn)
        btns.addWidget(self.ai_decompose_btn)

        header.addLayout(info, 1)
        header.addLayout(btns)
        parent_layout.addWidget(self.header_widget)

    # --- list ---

    def refresh_list(self, *_args, select_id: str | None = None) -> None:
        cid = select_id or (self.current_plan.id if self.current_plan else None)
        blocker = QSignalBlocker(self.plan_list)
        self.plan_list.clear()
        target = -1
        q = self.search_input.text() if hasattr(self, "search_input") else ""
        sf = self.status_filter.currentText() if hasattr(self, "status_filter") else "全部"
        for row, plan in enumerate(self.storage.list_plans(q, sf)):
            item = QListWidgetItem(f"{plan.display_title}\n{plan.plan_type} | {plan.status} | {plan.progress}%")
            item.setData(Qt.ItemDataRole.UserRole, plan.id)
            self.plan_list.addItem(item)
            if cid and plan.id == cid:
                target = row
        del blocker
        if target >= 0:
            self.plan_list.setCurrentRow(target)

    def new_plan(self) -> None:
        if not self._maybe_keep_changes():
            return
        plan = self.storage.create_empty_plan()
        dlg = _PlanEditDialog(plan, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        dlg.apply_to(plan)
        saved = self.storage.save_plan(plan)
        self._load_plan(saved)
        self.refresh_list(select_id=saved.id)
        self._show_status("已创建行动计划。", 3000)

    def delete_current_plan(self) -> None:
        if self.current_plan is None:
            return
        if not self.storage.plan_dir(self.current_plan.id).exists():
            QMessageBox.information(self, "提示", "该计划尚未保存。")
            return
        reply = QMessageBox.question(
            self, "删除确认", f"确定删除「{self.current_plan.display_title}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.storage.delete_plan(self.current_plan.id)
        self.current_plan = None
        self._set_dirty(False)
        self.refresh_list()
        self._show_empty_state()
        self._show_status("已删除行动计划。", 3000)

    def open_plan_by_id(self, plan_id: str) -> None:
        try:
            plan = self.storage.load_plan(plan_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取行动计划时出错：\n{exc}")
            return
        self._load_plan(plan)
        self.refresh_list(select_id=plan.id)

    # --- plan ops ---

    def _edit_plan(self) -> None:
        if self.current_plan is None:
            return
        dlg = _PlanEditDialog(self.current_plan, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        dlg.apply_to(self.current_plan)
        self.storage.save_plan(self.current_plan)
        self._refresh_header()
        self.refresh_list(select_id=self.current_plan.id)
        self._mark_dirty()
        self._show_status("已更新计划信息。", 3000)

    def _ai_decompose(self) -> None:
        if self.current_plan is None:
            return
        from .ai_dialogs import AIPreviewDialog
        from .ai_service import call_ai_json

        plan = self.current_plan
        dlg = _DecomposeDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        system = (
            "你是项目计划助手。只返回 JSON。格式："
            '{"title":"","plan_type":"","description":"","start_date":"","end_date":"",'
            '"daily_available_time":"","priority":"","tasks":['
            '{"date":"YYYY-MM-DD","title":"","estimated_minutes":30,"note":""}]}'
        )
        user = (
            f"标题: {plan.title}\n描述: {plan.description}\n类型: {plan.plan_type}\n"
            f"优先级: {plan.priority}\n开始: {dlg.start_date}\n截止: {dlg.end_date}\n"
            f"每日可用: {dlg.daily_time}\n请拆解为按日期排列的任务。"
        )
        try:
            result = call_ai_json(str(self.storage.root_dir), system, user, temperature=0.3)
        except Exception as exc:
            QMessageBox.warning(self, "AI 调用失败", str(exc))
            return

        tasks_data = result.get("tasks", [])
        if not tasks_data:
            QMessageBox.warning(self, "AI 返回为空", "AI 未生成任务，请调整描述后重试。")
            return

        preview = [
            f"标题: {result.get('title', plan.title)}",
            f"类型: {result.get('plan_type', plan.plan_type)}",
            f"日期: {result.get('start_date', '')} ~ {result.get('end_date', '')}",
            f"每日: {result.get('daily_available_time', '')}",
            f"任务数: {len(tasks_data)}", "",
        ]
        for i, t in enumerate(tasks_data, 1):
            preview.append(f"  {i}. [{t.get('date','')}] {t.get('title','')} ({t.get('estimated_minutes',30)}分钟)")

        pdlg = AIPreviewDialog("AI 拆解预览", "\n".join(preview), parent=self)
        if pdlg.exec() != QDialog.DialogCode.Accepted or not pdlg.is_confirmed:
            return

        plan.title = str(result.get("title", plan.title))
        plan.plan_type = str(result.get("plan_type", plan.plan_type))
        plan.description = str(result.get("description", plan.description))
        plan.start_date = str(result.get("start_date", dlg.start_date))
        plan.end_date = str(result.get("end_date", dlg.end_date))
        plan.daily_available_time = str(result.get("daily_available_time", dlg.daily_time))
        plan.priority = str(result.get("priority", plan.priority))
        plan.tasks = [
            ActionPlanTask(
                id=_uuid4().hex,
                title=str(t.get("title", "")),
                date=str(t.get("date", "")),
                estimated_minutes=int(t.get("estimated_minutes", 30)),
                note=str(t.get("note", "")),
            )
            for t in tasks_data
        ]
        saved = self.storage.save_plan(plan)
        self._load_plan(saved)
        self.refresh_list(select_id=saved.id)
        self._show_status("AI 拆解完成，已更新任务列表。", 5000)

    # --- task ops ---

    def _add_task(self) -> None:
        if self.current_plan is None:
            return
        dlg = _TaskEditDialog(parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        task = dlg.result
        self.current_plan.tasks.append(task)
        self._save_and_refresh()

    def _edit_selected_task(self) -> None:
        if self.current_plan is None:
            return
        task = self._selected_task()
        if task is None:
            QMessageBox.information(self, "提示", "请在任务链模式双击选择一个任务节点。")
            return
        dlg = _TaskEditDialog(task, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._save_and_refresh()

    def _delete_selected_task(self) -> None:
        if self.current_plan is None:
            return
        task = self._selected_task()
        if task is None:
            return
        reply = QMessageBox.question(
            self, "删除确认", f"确定删除任务「{task.title}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.current_plan.tasks = [t for t in self.current_plan.tasks if t.id != task.id]
        self._save_and_refresh()

    def _selected_task(self) -> ActionPlanTask | None:
        if self._chain_view is None:
            return None
        selected = self._chain_view._scene.selectedItems()
        if selected:
            for it in selected:
                if isinstance(it, _TaskNode):
                    return it.task
        return None

    def _toggle_task(self, task: ActionPlanTask, done: bool) -> None:
        task.done = done
        self._save_and_refresh()

    def _edit_task_direct(self, task: ActionPlanTask) -> None:
        dlg = _TaskEditDialog(task, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._save_and_refresh()

    def _save_and_refresh(self) -> None:
        if self.current_plan is None:
            return
        if self._chain_view is not None:
            pos = self._chain_view.collect_positions()
            for t in self.current_plan.tasks:
                if t.id in pos:
                    t.x, t.y = pos[t.id]
        saved = self.storage.save_plan(self.current_plan)
        self._load_plan(saved)
        self._mark_dirty()

    # --- load ---

    def _load_plan(self, plan: ActionPlanItem) -> None:
        self.current_plan = plan
        self._refresh_header()
        self._refresh_views()
        self._set_dirty(False)

    def _refresh_header(self) -> None:
        if self.current_plan is None:
            return
        self.plan_title_label.setText(self.current_plan.display_title)
        self.plan_meta_label.setText(
            f"{self.current_plan.plan_type} | {self.current_plan.status} | "
            f"{self.current_plan.priority} | "
            f"{self.current_plan.start_date} ~ {self.current_plan.end_date} | "
            f"每日 {self.current_plan.daily_available_time or '未设'}"
        )
        self.progress_bar.setValue(int(self.current_plan.progress))

    def _refresh_views(self) -> None:
        if self.current_plan is None:
            return
        tasks = self.current_plan.tasks
        self._timeline.load_tasks(tasks, self._toggle_task, self._edit_task_direct)
        if self._chain_view is not None:
            self._chain_view.load_tasks(tasks, self._toggle_task, self._edit_task_direct)

    def _on_mode_changed(self, index: int) -> None:
        if index == 1:
            if self._chain_view is None:
                try:
                    self._chain_view = _TaskChainView(self)
                    self._mode_tabs.removeTab(1)
                    self._mode_tabs.addTab(self._chain_view, "任务链")
                except Exception:
                    return
            if self.current_plan:
                self._chain_view.load_tasks(
                    self.current_plan.tasks, self._toggle_task, self._edit_task_direct
                )

    def _show_empty_state(self) -> None:
        self.plan_title_label.setText("选择一个行动计划或新建")
        self.plan_meta_label.setText("")
        self.progress_bar.setValue(0)
        self._timeline.load_tasks([], self._toggle_task, self._edit_task_direct)
        if self._chain_view is not None:
            self._chain_view.load_tasks([], self._toggle_task, self._edit_task_direct)

    # --- select ---

    def _on_select(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.plan_list)
            self.plan_list.setCurrentItem(previous)
            del blocker
            return
        pid = current.data(Qt.ItemDataRole.UserRole)
        if self.current_plan and self.current_plan.id == pid:
            return
        try:
            plan = self.storage.load_plan(pid)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取行动计划时出错：\n{exc}")
            return
        self._load_plan(plan)
        self.refresh_list(select_id=plan.id)

    # --- autosave ---

    def _mark_dirty(self, *_args) -> None:
        self._set_dirty(True)

    def _set_dirty(self, dirty: bool) -> None:
        if self.is_dirty == dirty:
            if dirty:
                self._on_dirty_state_changed_for_autosave(True)
            return
        self.is_dirty = dirty
        self.dirty_state_changed.emit(dirty)
        self._on_dirty_state_changed_for_autosave(dirty)

    def _maybe_keep_changes(self) -> bool:
        return self.maybe_finish_pending_changes()

    def _auto_save_now(self) -> bool:
        if self.current_plan is None:
            return True
        if self._chain_view is not None:
            pos = self._chain_view.collect_positions()
            for t in self.current_plan.tasks:
                if t.id in pos:
                    t.x, t.y = pos[t.id]
        try:
            self.storage.save_plan(self.current_plan)
        except Exception:
            return False
        self._set_dirty(False)
        return True

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_plan is None:
            return False
        return bool(self.current_plan.title.strip() or self.current_plan.tasks)

    def _show_status(self, msg: str, timeout: int = 3000) -> None:
        w = self.window()
        if hasattr(w, "statusBar"):
            w.statusBar().showMessage(msg, timeout)


class _DecomposeDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("AI 拆解 — 时间设置")
        self.setMinimumWidth(400)
        lo = QVBoxLayout(self)
        form = QFormLayout()
        self.start_edit = QDateEdit(QDate.currentDate(), self)
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_edit = QDateEdit(QDate.currentDate().addDays(7), self)
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat("yyyy-MM-dd")
        self.daily_input = QLineEdit(self)
        self.daily_input.setPlaceholderText("例如: 1小时")
        form.addRow("开始日期", self.start_edit)
        form.addRow("截止日期", self.end_edit)
        form.addRow("每日可用时间", self.daily_input)
        lo.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        lo.addWidget(btns)

    def _validate(self) -> None:
        if self.start_edit.date() > self.end_edit.date():
            QMessageBox.warning(self, "日期错误", "开始日期不能晚于截止日期。")
            return
        self.accept()

    @property
    def start_date(self) -> str:
        return self.start_edit.date().toString("yyyy-MM-dd")

    @property
    def end_date(self) -> str:
        return self.end_edit.date().toString("yyyy-MM-dd")

    @property
    def daily_time(self) -> str:
        return self.daily_input.text().strip() or "1小时"
