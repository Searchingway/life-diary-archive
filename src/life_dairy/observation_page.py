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
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .autosave import AutoSaveMixin
from .observation_storage import OBSERVATION_EMOTIONS, OBSERVATION_NEEDS, ObservationEntry, ObservationStorage
from .self_analysis_storage import SelfAnalysisStorage
from .ui_helpers import make_scroll_area


class ObservationPage(AutoSaveMixin, QWidget):
    dirty_state_changed = Signal(bool)
    analysis_created = Signal(str)

    def __init__(
        self,
        storage: ObservationStorage,
        self_analysis_storage: SelfAnalysisStorage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.self_analysis_storage = self_analysis_storage
        self.current_observation: ObservationEntry | None = None
        self.is_dirty = False
        self._is_loading_form = False
        self._build_ui()
        self._init_auto_save()
        self.refresh_observation_list()
        if self.observation_list.count() > 0 and self.observation_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.observation_list.setCurrentRow(0)
        else:
            self.new_observation()

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
        splitter.setSizes([310, 860])
        layout.addWidget(make_scroll_area(splitter))

    def _build_sidebar(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel("自我观察", widget)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.search_input = QLineEdit(widget)
        self.search_input.setPlaceholderText("搜索触发原因 / 身体感受 / 需要")
        self.search_input.textChanged.connect(self.refresh_observation_list)
        self.emotion_filter_combo = QComboBox(widget)
        self.emotion_filter_combo.addItems(["全部", *OBSERVATION_EMOTIONS])
        self.emotion_filter_combo.currentTextChanged.connect(self.refresh_observation_list)
        self.intensity_filter_combo = QComboBox(widget)
        self.intensity_filter_combo.addItems(["全部", "1", "2", "3", "4", "5"])
        self.intensity_filter_combo.currentTextChanged.connect(self.refresh_observation_list)
        self.date_filter_input = QLineEdit(widget)
        self.date_filter_input.setPlaceholderText("日期筛选，例如 2026-05 或 2026-05-02")
        self.date_filter_input.textChanged.connect(self.refresh_observation_list)
        self.new_button = QPushButton("新建自我观察", widget)
        self.new_button.clicked.connect(self.new_observation)
        self.delete_button = QPushButton("删除当前记录", widget)
        self.delete_button.clicked.connect(self.delete_current_observation)
        self.observation_list = QListWidget(widget)
        self.observation_list.currentItemChanged.connect(self._on_current_item_changed)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.emotion_filter_combo)
        layout.addWidget(self.intensity_filter_combo)
        layout.addWidget(self.date_filter_input)
        layout.addWidget(self.new_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.observation_list, 1)
        return widget

    def _build_editor(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.save_button = QPushButton("保存", widget)
        self.save_button.clicked.connect(self.save_observation)
        self.reload_button = QPushButton("恢复已保存内容", widget)
        self.reload_button.clicked.connect(self.reload_current_observation)
        self.to_analysis_button = QPushButton("转为自我分析", widget)
        self.to_analysis_button.clicked.connect(self.convert_to_self_analysis)
        action_row.addWidget(self.save_button)
        action_row.addWidget(self.reload_button)
        action_row.addWidget(self.to_analysis_button)
        action_row.addStretch(1)

        group = QGroupBox("观察详情", widget)
        group_layout = QVBoxLayout(group)
        form = QFormLayout()
        self.time_input = QLineEdit(group)
        self.time_input.setPlaceholderText("观察时间，例如 2026-05-02T20:30:00+08:00")
        self.time_input.textChanged.connect(self._mark_dirty)
        self.emotion_combo = QComboBox(group)
        self.emotion_combo.addItems(OBSERVATION_EMOTIONS)
        self.emotion_combo.currentTextChanged.connect(self._mark_dirty)
        self.intensity_spin = QSpinBox(group)
        self.intensity_spin.setRange(1, 5)
        self.intensity_spin.valueChanged.connect(self._mark_dirty)
        self.need_combo = QComboBox(group)
        self.need_combo.addItems(OBSERVATION_NEEDS)
        self.need_combo.currentTextChanged.connect(self._mark_dirty)
        form.addRow("时间", self.time_input)
        form.addRow("情绪", self.emotion_combo)
        form.addRow("强度", self.intensity_spin)
        form.addRow("当前需要", self.need_combo)
        group_layout.addLayout(form)

        self.trigger_edit = self._make_text_edit("触发原因：刚刚发生了什么？")
        self.body_edit = self._make_text_edit("身体感受：胸口、胃、肩颈、呼吸等。")
        self.notes_edit = self._make_text_edit("补充记录")
        group_layout.addWidget(QLabel("触发原因", group))
        group_layout.addWidget(self.trigger_edit)
        group_layout.addWidget(QLabel("身体感受", group))
        group_layout.addWidget(self.body_edit)
        group_layout.addWidget(QLabel("补充记录", group))
        group_layout.addWidget(self.notes_edit)

        hint = QLabel("这里承接手机版的“我现在感觉怎么样”；点击“转为自我分析”后，再进入更深的“我为什么反复这样感觉”。", widget)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #526157;")
        layout.addLayout(action_row)
        layout.addWidget(group, 1)
        layout.addWidget(hint)
        return widget

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        edit = QTextEdit(self)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(100)
        edit.textChanged.connect(self._mark_dirty)
        return edit

    def refresh_observation_list(self, *_args, select_id: str | None = None) -> None:
        current_id = select_id or (self.current_observation.id if self.current_observation is not None else None)
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        emotion = self.emotion_filter_combo.currentText() if hasattr(self, "emotion_filter_combo") else "全部"
        intensity = self.intensity_filter_combo.currentText() if hasattr(self, "intensity_filter_combo") else "全部"
        date_prefix = self.date_filter_input.text().strip() if hasattr(self, "date_filter_input") else ""
        blocker = QSignalBlocker(self.observation_list)
        self.observation_list.clear()
        target_row = -1
        for row, observation in enumerate(self.storage.list_observations(query, emotion, intensity, date_prefix)):
            item = QListWidgetItem(self._build_list_text(observation))
            item.setData(Qt.ItemDataRole.UserRole, observation.id)
            item.setToolTip(observation.trigger or observation.body_sensation or observation.display_title)
            self.observation_list.addItem(item)
            if current_id and observation.id == current_id:
                target_row = row
        if target_row >= 0:
            self.observation_list.setCurrentRow(target_row)
        del blocker
        if self.observation_list.count() == 0:
            self.observation_list.addItem("暂无自我观察记录。")

    def new_observation(self) -> None:
        if not self._maybe_keep_changes():
            return
        self._fill_form(self.storage.create_empty_observation())
        self.observation_list.blockSignals(True)
        self.observation_list.clearSelection()
        self.observation_list.blockSignals(False)
        self._show_status("已创建新的自我观察草稿。", 3000)

    def save_observation(self) -> bool:
        observation = self._read_form()
        try:
            saved = self.storage.save_observation(observation)
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", f"保存自我观察时出错：\n{exc}")
            return False
        self._fill_form(saved)
        self.refresh_observation_list(select_id=saved.id)
        self._show_status("自我观察已保存。", 3000)
        return True

    def reload_current_observation(self) -> None:
        if self.current_observation is None or not self.storage.observation_dir(self.current_observation.id).exists():
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
            observation = self.storage.load_observation(self.current_observation.id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取自我观察时出错：\n{exc}")
            return
        self._fill_form(observation)
        self.refresh_observation_list(select_id=observation.id)

    def delete_current_observation(self) -> None:
        if self.current_observation is None:
            return
        if not self.storage.observation_dir(self.current_observation.id).exists():
            reply = QMessageBox.question(self, "放弃草稿", "这条自我观察还没保存，确定放弃吗？")
            if reply == QMessageBox.StandardButton.Yes:
                self._discard_current_draft("已放弃未保存的自我观察草稿。")
            return
        reply = QMessageBox.question(
            self,
            "删除确认",
            f"确定删除这条自我观察吗？\n\n{self.current_observation.display_title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.storage.delete_observation(self.current_observation.id)
        except Exception as exc:
            QMessageBox.critical(self, "删除失败", f"删除自我观察时出错：\n{exc}")
            return
        self._discard_current_draft("已删除当前自我观察。")

    def convert_to_self_analysis(self) -> None:
        if self.current_observation is None:
            return
        observation = self._read_form()
        analysis = self.self_analysis_storage.create_empty_analysis()
        analysis.title = f"{observation.emotion}的反复观察"
        analysis.date = observation.date
        analysis.analysis_type = "情绪"
        analysis.trigger_event = observation.trigger
        analysis.emotion = f"{observation.emotion}，强度 {observation.intensity}"
        analysis.body_reaction = observation.body_sensation
        analysis.surface_want = observation.need
        analysis.insight = observation.notes
        saved = self.self_analysis_storage.save_analysis(analysis)
        self.analysis_created.emit(saved.id)
        self._show_status("已创建自我分析草稿。", 4000)

    def open_observation_by_id(self, observation_id: str, status_message: str | None = None) -> None:
        try:
            observation = self.storage.load_observation(observation_id)
        except Exception as exc:
            QMessageBox.critical(self, "读取失败", f"读取自我观察时出错：\n{exc}")
            return
        self._fill_form(observation)
        self.refresh_observation_list(select_id=observation.id)
        if status_message:
            self._show_status(status_message, 3000)

    def _fill_form(self, observation: ObservationEntry) -> None:
        self._is_loading_form = True
        self.current_observation = observation
        try:
            self.time_input.setText(observation.time)
            self._set_combo_text(self.emotion_combo, observation.emotion)
            self.intensity_spin.setValue(observation.intensity)
            self._set_combo_text(self.need_combo, observation.need)
            self.trigger_edit.setPlainText(observation.trigger)
            self.body_edit.setPlainText(observation.body_sensation)
            self.notes_edit.setPlainText(observation.notes)
            self._set_dirty(False)
        finally:
            self._is_loading_form = False

    def _read_form(self) -> ObservationEntry:
        if self.current_observation is None:
            self.current_observation = self.storage.create_empty_observation()
        self.current_observation.time = self.time_input.text().strip()
        self.current_observation.emotion = self.emotion_combo.currentText().strip() or "其他"
        self.current_observation.intensity = self.intensity_spin.value()
        self.current_observation.need = self.need_combo.currentText().strip() or "其他"
        self.current_observation.trigger = self.trigger_edit.toPlainText()
        self.current_observation.body_sensation = self.body_edit.toPlainText()
        self.current_observation.notes = self.notes_edit.toPlainText()
        return self.current_observation

    def _on_current_item_changed(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        if current is None:
            return
        observation_id = current.data(Qt.ItemDataRole.UserRole)
        if not observation_id:
            return
        if not self._maybe_keep_changes():
            blocker = QSignalBlocker(self.observation_list)
            self.observation_list.setCurrentItem(previous)
            del blocker
            return
        if self.current_observation is not None and self.current_observation.id == observation_id:
            return
        self.open_observation_by_id(observation_id, status_message="已打开这条自我观察。")

    def _discard_current_draft(self, status_message: str) -> None:
        self.current_observation = None
        self._set_dirty(False)
        self.refresh_observation_list()
        if self.observation_list.count() > 0 and self.observation_list.item(0).data(Qt.ItemDataRole.UserRole):
            self.observation_list.setCurrentRow(0)
        else:
            self.new_observation()
        self._show_status(status_message, 3000)

    def _build_list_text(self, observation: ObservationEntry) -> str:
        return f"{observation.date} | {observation.display_title}\n{observation.trigger or observation.need}"

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
        observation = self._read_form()
        try:
            self.storage.save_observation(observation)
        except Exception:
            return False
        self._set_dirty(False)
        return True

    def _auto_save_has_meaningful_content(self) -> bool:
        if self.current_observation is None:
            return False
        if self.storage.observation_dir(self.current_observation.id).exists():
            return True
        return bool(
            self.trigger_edit.toPlainText().strip()
            or self.body_edit.toPlainText().strip()
            or self.notes_edit.toPlainText().strip()
        )

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, timeout)
