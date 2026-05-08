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
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .autosave import AutoSaveMixin
from .info_memo_storage import (
    ALL_STATUSES,
    DIRECTIONS,
    GENERAL_CATEGORIES,
    GENERAL_STATUSES,
    INFO_MEMO_TYPES,
    ORDER_STATUSES,
    PRIORITIES,
    STATUS_MAP,
    InfoMemoEntry,
    InfoMemoStorage,
    _parse_amount,
)
from .ui_helpers import make_scroll_area


TYPE_PAGE_MAP = {"接单记录": 0, "网课资源": 1, "通用信息": 2}


class InfoMemoPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)

    def __init__(self, storage: InfoMemoStorage, parent: QWidget | None = None):
        super().__init__(parent)
        self.storage = storage
        self.current_memo: InfoMemoEntry | None = None
        self.is_dirty = False
        self._is_loading_form = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_info_memo_list()
        if self.memo_list.count() > 0 and self.memo_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.memo_list.setCurrentRow(0)
        else:
            self.new_memo()

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

        title = QLabel("信息备忘", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索标题 / 标签 / 来源 / 链接 / 备注 / 客户 / 课程")
        self.search_input.textChanged.connect(self._on_search_changed)

        self.type_filter_combo = QComboBox(widget)
        self.type_filter_combo.addItems(["全部", *INFO_MEMO_TYPES])
        self.type_filter_combo.currentTextChanged.connect(self._on_type_filter_changed)

        self.status_filter_combo = QComboBox(widget)
        self._fill_status_filter("全部")
        self.status_filter_combo.currentTextChanged.connect(self.refresh_info_memo_list)

        self.new_button = QPushButton("新建信息卡片", widget)
        self.new_button.clicked.connect(self.new_memo)
        self.delete_button = QPushButton("删除当前记录", widget)
        self.delete_button.clicked.connect(self.delete_current_memo)
        self.memo_list = QListWidget(widget)
        self.memo_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.type_filter_combo)
        layout.addWidget(self.status_filter_combo)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.memo_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_memo)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_memo)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addStretch(1)

        common_group = QGroupBox("基本信息", widget)
        common_layout = QVBoxLayout(common_group)
        form = QFormLayout()
        self.title_input = QLineEdit(common_group)
        self.title_input.setPlaceholderText("标题")
        self.title_input.textChanged.connect(self._mark_dirty)
        self.type_combo = QComboBox(common_group)
        self.type_combo.addItems(INFO_MEMO_TYPES)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.status_combo = QComboBox(common_group)
        self.status_combo.addItems(ORDER_STATUSES)
        self.status_combo.currentTextChanged.connect(self._mark_dirty)
        self.priority_combo = QComboBox(common_group)
        self.priority_combo.addItems(PRIORITIES)
        self.priority_combo.currentTextChanged.connect(self._mark_dirty)
        self.tags_input = QLineEdit(common_group)
        self.tags_input.setPlaceholderText("用逗号分隔")
        self.tags_input.textChanged.connect(self._mark_dirty)
        self.source_input = QLineEdit(common_group)
        self.source_input.setPlaceholderText("来源 / 介绍人")
        self.source_input.textChanged.connect(self._mark_dirty)
        self.link_input = QLineEdit(common_group)
        self.link_input.setPlaceholderText("https://...")
        self.link_input.textChanged.connect(self._mark_dirty)
        self.local_path_input = QLineEdit(common_group)
        self.local_path_input.setPlaceholderText("本地文件夹路径")
        self.local_path_input.textChanged.connect(self._mark_dirty)
        form.addRow("标题", self.title_input)
        form.addRow("类型", self.type_combo)
        form.addRow("状态", self.status_combo)
        form.addRow("优先级", self.priority_combo)
        form.addRow("标签", self.tags_input)
        form.addRow("来源", self.source_input)
        form.addRow("相关链接", self.link_input)
        form.addRow("本地路径", self.local_path_input)
        common_layout.addLayout(form)
        self.note_edit = self._make_text_edit("补充备注")
        common_layout.addWidget(QLabel("备注", common_group))
        common_layout.addWidget(self.note_edit)

        type_group = QGroupBox("详细信息", widget)
        type_layout = QVBoxLayout(type_group)
        self.type_specific_stack = QStackedWidget(type_group)
        self.type_specific_stack.addWidget(self._build_order_form())
        self.type_specific_stack.addWidget(self._build_course_form())
        self.type_specific_stack.addWidget(self._build_general_form())
        type_layout.addWidget(self.type_specific_stack)

        layout.addLayout(action_row)
        layout.addWidget(common_group, 2)
        layout.addWidget(type_group, 2)
        return widget

    def _build_order_form(self) -> QWidget:
        page = QWidget(self)
        layout = QFormLayout(page)
        layout.setSpacing(8)

        self.order_customer_input = QLineEdit(page)
        self.order_customer_input.setPlaceholderText("客户 / 需求方")
        self.order_customer_input.textChanged.connect(self._mark_dirty)
        self.order_intermediary_input = QLineEdit(page)
        self.order_intermediary_input.setPlaceholderText("中介 / 介绍人")
        self.order_intermediary_input.textChanged.connect(self._mark_dirty)
        self.order_executor_input = QLineEdit(page)
        self.order_executor_input.setPlaceholderText("实际执行人")
        self.order_executor_input.textChanged.connect(self._mark_dirty)
        self.order_date_input = QLineEdit(page)
        self.order_date_input.setPlaceholderText("如 2026-01-15")
        self.order_date_input.textChanged.connect(self._mark_dirty)
        self.order_deadline_input = QLineEdit(page)
        self.order_deadline_input.setPlaceholderText("如 2026-02-15")
        self.order_deadline_input.textChanged.connect(self._mark_dirty)
        self.order_duration_input = QSpinBox(page)
        self.order_duration_input.setRange(0, 9999)
        self.order_duration_input.setSuffix(" 天")
        self.order_duration_input.setSpecialValueText("未设置")
        self.order_duration_input.valueChanged.connect(self._mark_dirty)
        self.order_price_input = QLineEdit(page)
        self.order_price_input.setPlaceholderText("输入金额，如 800")
        self.order_price_input.textChanged.connect(self._on_order_price_or_deposit_changed)
        self.order_price_input.textChanged.connect(self._mark_dirty)
        self.order_deposit_input = QLineEdit(page)
        self.order_deposit_input.setPlaceholderText("默认为 0")
        self.order_deposit_input.textChanged.connect(self._on_order_price_or_deposit_changed)
        self.order_deposit_input.textChanged.connect(self._mark_dirty)
        self.order_final_payment_input = QLineEdit(page)
        self.order_final_payment_input.setPlaceholderText("自动计算：报价 - 定金")
        self.order_final_payment_input.setReadOnly(True)
        self.order_final_payment_input.setStyleSheet("background: #f5f5f5;")
        self.order_deliverables_edit = QTextEdit(page)
        self.order_deliverables_edit.setPlaceholderText("交付内容说明")
        self.order_deliverables_edit.setMinimumHeight(80)
        self.order_deliverables_edit.textChanged.connect(self._mark_dirty)

        layout.addRow("客户/需求方", self.order_customer_input)
        layout.addRow("中介/介绍人", self.order_intermediary_input)
        layout.addRow("实际执行人", self.order_executor_input)
        layout.addRow("接单日期", self.order_date_input)
        layout.addRow("截止日期", self.order_deadline_input)
        layout.addRow("工期天数", self.order_duration_input)
        layout.addRow("报价 (¥)", self.order_price_input)
        layout.addRow("定金 (¥)", self.order_deposit_input)
        layout.addRow("尾款 (¥)", self.order_final_payment_input)
        layout.addRow("交付内容", self.order_deliverables_edit)
        return page

    def _format_amount(self, value: float | str) -> str:
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return "0.00"

    def _update_final_payment(self) -> None:
        price = _parse_amount(self.order_price_input.text())
        deposit = _parse_amount(self.order_deposit_input.text())
        final_payment = round(max(0, price - deposit), 2)
        self.order_final_payment_input.setText(self._format_amount(final_payment))

    def _on_order_price_or_deposit_changed(self, *_args) -> None:
        if self._is_loading_form:
            return
        self._update_final_payment()

    def _build_course_form(self) -> QWidget:
        page = QWidget(self)
        layout = QFormLayout(page)
        layout.setSpacing(8)

        self.course_name_input = QLineEdit(page)
        self.course_name_input.setPlaceholderText("课程名称")
        self.course_name_input.textChanged.connect(self._mark_dirty)
        self.course_platform_input = QLineEdit(page)
        self.course_platform_input.setPlaceholderText("平台 / 网站")
        self.course_platform_input.textChanged.connect(self._mark_dirty)
        self.course_url_input = QLineEdit(page)
        self.course_url_input.setPlaceholderText("https://...")
        self.course_url_input.textChanged.connect(self._mark_dirty)
        self.course_direction_combo = QComboBox(page)
        self.course_direction_combo.addItems(DIRECTIONS)
        self.course_direction_combo.currentTextChanged.connect(self._mark_dirty)
        self.course_paid_input = QLineEdit(page)
        self.course_paid_input.setPlaceholderText("免费 / 已购 / 待购")
        self.course_paid_input.textChanged.connect(self._mark_dirty)
        self.course_progress_input = QLineEdit(page)
        self.course_progress_input.setPlaceholderText("如 30% / 第5章")
        self.course_progress_input.textChanged.connect(self._mark_dirty)
        self.course_reason_edit = QTextEdit(page)
        self.course_reason_edit.setPlaceholderText("为什么想学？")
        self.course_reason_edit.setMinimumHeight(80)
        self.course_reason_edit.textChanged.connect(self._mark_dirty)

        layout.addRow("课程名称", self.course_name_input)
        layout.addRow("平台/网站", self.course_platform_input)
        layout.addRow("课程链接", self.course_url_input)
        layout.addRow("学习方向", self.course_direction_combo)
        layout.addRow("购买状态", self.course_paid_input)
        layout.addRow("当前进度", self.course_progress_input)
        layout.addRow("想学原因", self.course_reason_edit)
        return page

    def _build_general_form(self) -> QWidget:
        page = QWidget(self)
        layout = QFormLayout(page)
        layout.setSpacing(8)

        self.general_category_combo = QComboBox(page)
        self.general_category_combo.addItems(GENERAL_CATEGORIES)
        self.general_category_combo.currentTextChanged.connect(self._mark_dirty)
        self.general_content_edit = QTextEdit(page)
        self.general_content_edit.setPlaceholderText("主要内容")
        self.general_content_edit.setMinimumHeight(100)
        self.general_content_edit.textChanged.connect(self._mark_dirty)
        self.general_reminder_input = QLineEdit(page)
        self.general_reminder_input.setPlaceholderText("可选，如 2026-06-01")
        self.general_reminder_input.textChanged.connect(self._mark_dirty)

        layout.addRow("分类", self.general_category_combo)
        layout.addRow("主要内容", self.general_content_edit)
        layout.addRow("提醒日期", self.general_reminder_input)
        return page

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit(self)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(78)
        edit.textChanged.connect(self._mark_dirty)
        return edit

    def _fill_status_filter(self, selected_type: str) -> None:
        if selected_type in STATUS_MAP:
            statuses = ["全部", *STATUS_MAP[selected_type]]
        else:
            statuses = ["全部", *ALL_STATUSES]
        current = self.status_filter_combo.currentText() if hasattr(self, "status_filter_combo") else "全部"
        blocker = QSignalBlocker(self.status_filter_combo) if hasattr(self, "status_filter_combo") else None
        self.status_filter_combo.clear()
        self.status_filter_combo.addItems(statuses)
        if current in statuses:
            idx = self.status_filter_combo.findText(current)
            if idx >= 0:
                self.status_filter_combo.setCurrentIndex(idx)
        if blocker:
            del blocker

    def refresh_info_memo_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id or (self.current_memo.id if self.current_memo is not None else None)
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        info_type = self.type_filter_combo.currentText() if hasattr(self, "type_filter_combo") else "全部"
        status = self.status_filter_combo.currentText() if hasattr(self, "status_filter_combo") else "全部"
        blocker = QSignalBlocker(self.memo_list)
        self.memo_list.clear()
        target_row = -1
        for row, memo in enumerate(self.storage.list_info_memos(query, info_type, status)):
            item = QListWidgetItem(self._build_list_text(memo))
            item.setData(Qt.ItemDataRole.UserRole, memo.id)
            tip = memo.note or ""
            if not tip and memo.type_fields:
                tf = memo.type_fields
                tip = str(tf.get("content", "") or tf.get("deliverables", "") or tf.get("reason", "") or "")
            item.setToolTip(tip or memo.display_title)
            self.memo_list.addItem(item)
            if current_id and memo.id == current_id:
                target_row = row
        if target_row >= 0:
            self.memo_list.setCurrentRow(target_row)
        del blocker
        if self.memo_list.count() == 0:
            self.memo_list.addItem("暂无信息备忘记录。")

    def new_memo(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_memo())
        self.memo_list.blockSignals(True)
        self.memo_list.clearSelection()
        self.memo_list.blockSignals(False)
        self._show_status("已创建新的信息卡片草稿。", 3000)

    def save_memo(self) -> bool:
        memo = self._read_form()
        try:
            saved = self.storage.save_memo(memo)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存信息备忘时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_info_memo_list(select_id=saved.id)
        self._show_status("信息备忘已保存。", 3000)
        return True

    def reload_current_memo(self) -> None:
        if self.current_memo is None or not self.storage.memo_dir(self.current_memo.id).exists():
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
            memo = self.storage.load_memo(self.current_memo.id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取信息备忘时出错：\n{exc}")
            return
        self._fill_form(memo)
        self.refresh_info_memo_list(select_id=memo.id)

    def delete_current_memo(self) -> None:
        if self.current_memo is None:
            return
        if not self.storage.memo_dir(self.current_memo.id).exists():
            reply = QMessageBox.question(self, "放弃草稿", "这条信息还没保存，确定放弃吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self._discard_current_draft("已放弃未保存的信息卡片草稿。")
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定删除这条信息卡片吗？\n\n{self.current_memo.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_memo(self.current_memo.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除信息备忘时出错：\n{exc}")
            return
        self._discard_current_draft("已删除当前信息卡片。")

    def open_memo_by_id(self, memo_id: str, status_message: str | None = None) -> None:
        try:
            memo = self.storage.load_memo(memo_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取信息备忘时出错：\n{exc}")
            return
        self._fill_form(memo)
        self.refresh_info_memo_list(select_id=memo.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _fill_form(self, memo: InfoMemoEntry) -> None:
        self._is_loading_form = True
        self.current_memo = memo
        try:
            self.title_input.setText(memo.title)
            self._set_combo_text(self.type_combo, memo.info_type)
            self._set_combo_text(self.status_combo, memo.status)
            self._set_combo_text(self.priority_combo, memo.priority)
            self.tags_input.setText(memo.tags)
            self.source_input.setText(memo.source)
            self.link_input.setText(memo.link)
            self.local_path_input.setText(memo.local_path)
            self.note_edit.setPlainText(memo.note)

            self._switch_type_page(memo.info_type)
            self._fill_type_fields(memo)
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _switch_type_page(self, info_type: str) -> None:
        page_index = TYPE_PAGE_MAP.get(info_type, 2)
        statuses = STATUS_MAP.get(info_type, GENERAL_STATUSES)
        current_status = self.status_combo.currentText() if hasattr(self, "status_combo") else ""
        blocker = QSignalBlocker(self.status_combo) if hasattr(self, "status_combo") else None
        self.status_combo.clear()
        self.status_combo.addItems(statuses)
        if current_status in statuses:
            self._set_combo_text(self.status_combo, current_status)
        if blocker:
            del blocker
        self.type_specific_stack.setCurrentIndex(page_index)

    def _fill_type_fields(self, memo: InfoMemoEntry) -> None:
        tf = memo.type_fields
        if memo.info_type == "接单记录":
            self.order_customer_input.setText(tf.get("customer", ""))
            self.order_intermediary_input.setText(tf.get("intermediary", ""))
            self.order_executor_input.setText(tf.get("executor", ""))
            self.order_date_input.setText(tf.get("order_date", ""))
            self.order_deadline_input.setText(tf.get("deadline", ""))
            self.order_duration_input.setValue(int(tf.get("duration_days", 0)))
            self.order_price_input.setText(self._format_amount(tf.get("price", 0)))
            self.order_deposit_input.setText(self._format_amount(tf.get("deposit", 0)))
            self._update_final_payment()
            self.order_deliverables_edit.setPlainText(tf.get("deliverables", ""))
        elif memo.info_type == "网课资源":
            self.course_name_input.setText(tf.get("course_name", ""))
            self.course_platform_input.setText(tf.get("platform", ""))
            self.course_url_input.setText(tf.get("course_url", ""))
            self._set_combo_text(self.course_direction_combo, tf.get("direction", ""))
            self.course_paid_input.setText(tf.get("paid_status", ""))
            self.course_progress_input.setText(tf.get("progress", ""))
            self.course_reason_edit.setPlainText(tf.get("reason", ""))
        else:
            self._set_combo_text(self.general_category_combo, tf.get("category", "其他"))
            self.general_content_edit.setPlainText(tf.get("content", ""))
            self.general_reminder_input.setText(tf.get("reminder_date", ""))

    def _read_form(self) -> InfoMemoEntry:
        if self.current_memo is None:
            self.current_memo = self.storage.create_empty_memo()
        self.current_memo.title = self.title_input.text().strip()
        info_type = self.type_combo.currentText().strip()
        self.current_memo.info_type = info_type if info_type in INFO_MEMO_TYPES else "通用信息"
        self.current_memo.status = self.status_combo.currentText().strip()
        self.current_memo.priority = self.priority_combo.currentText().strip() or "中"
        self.current_memo.tags = self.tags_input.text().strip()
        self.current_memo.source = self.source_input.text().strip()
        self.current_memo.link = self.link_input.text().strip()
        self.current_memo.local_path = self.local_path_input.text().strip()
        self.current_memo.note = self.note_edit.toPlainText()
        self._read_type_fields()
        return self.current_memo

    def _read_type_fields(self) -> None:
        if self.current_memo is None:
            return
        info_type = self.current_memo.info_type
        tf: dict = {}
        if info_type == "接单记录":
            tf["customer"] = self.order_customer_input.text().strip()
            tf["intermediary"] = self.order_intermediary_input.text().strip()
            tf["executor"] = self.order_executor_input.text().strip()
            tf["order_date"] = self.order_date_input.text().strip()
            tf["deadline"] = self.order_deadline_input.text().strip()
            tf["duration_days"] = self.order_duration_input.value()
            price = _parse_amount(self.order_price_input.text())
            deposit = _parse_amount(self.order_deposit_input.text())
            final_payment = round(max(0, price - deposit), 2)
            tf["price"] = price
            tf["deposit"] = deposit
            tf["final_payment"] = final_payment
            tf["deliverables"] = self.order_deliverables_edit.toPlainText().strip()
        elif info_type == "网课资源":
            tf["course_name"] = self.course_name_input.text().strip()
            tf["platform"] = self.course_platform_input.text().strip()
            tf["course_url"] = self.course_url_input.text().strip()
            tf["direction"] = self.course_direction_combo.currentText().strip()
            tf["paid_status"] = self.course_paid_input.text().strip()
            tf["progress"] = self.course_progress_input.text().strip()
            tf["reason"] = self.course_reason_edit.toPlainText().strip()
        else:
            tf["category"] = self.general_category_combo.currentText().strip()
            tf["content"] = self.general_content_edit.toPlainText().strip()
            tf["reminder_date"] = self.general_reminder_input.text().strip()
        self.current_memo.type_fields = tf

    def _on_type_filter_changed(self, text: str) -> None:
        self._fill_status_filter(text)
        self.refresh_info_memo_list()

    def _on_type_changed(self, info_type: str) -> None:
        if info_type not in INFO_MEMO_TYPES:
            return
        if not self._is_loading_form and self.current_memo is not None:
            self._read_type_fields()
        self._switch_type_page(info_type)
        if not self._is_loading_form and self.current_memo is not None:
            self.current_memo.info_type = info_type
            self._fill_type_fields(self.current_memo)
            self._mark_dirty()

    def _on_search_changed(self, text: str) -> None:
        self.refresh_info_memo_list()

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        memo_id = current.data(Qt.ItemDataRole.UserRole)
        if not memo_id:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.memo_list)
            self.memo_list.setCurrentItem(previous)
            del blocker
            return
        if self.current_memo is not None and self.current_memo.id == memo_id:
            return
        self.open_memo_by_id(memo_id, status_message="已打开这条信息备忘。")

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_memo = None
        self._set_dirty(False)
        self.refresh_info_memo_list()
        if self.memo_list.count() > 0 and self.memo_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.memo_list.setCurrentRow(0)
        else:
            self.new_memo()
        self._show_status(status_message, 3000)

    def _build_list_text(self, memo: InfoMemoEntry) -> str:
        return f"{memo.display_title}\n{memo.info_type} | {memo.status}"

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
        memo = self._read_form()
        try:
            self.storage.save_memo(memo)
        except Exception:
            return False
        self._set_dirty(False)
        return True

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_memo is None:
            return False
        if self.storage.memo_dir(self.current_memo.id).exists():
            return True
        return bool(self.title_input.text().strip() or self.note_edit.toPlainText().strip())

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
