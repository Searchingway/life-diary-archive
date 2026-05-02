from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTabWidget

from .backup_service import (
    APP_VERSION,
    create_backup,
    format_import_stats,
    import_mobile_backup,
    restore_backup,
    validate_backup,
    validate_mobile_backup,
)
from .book_storage import BookStorage
from .data_manager_page import DataManagerPage
from .diary_page import DiaryPage
from .footprint_page import FootprintPage
from .footprint_storage import FootprintStorage
from .lesson_page import LessonPage
from .lesson_storage import LessonStorage
from .observation_page import ObservationPage
from .observation_storage import ObservationStorage
from .overview import OverviewService
from .overview_page import OverviewPage
from .plan_page import PlanPage
from .plan_storage import PlanStorage
from .resource_page import ResourcePage
from .resource_storage import ResourceStorage
from .self_analysis_page import SelfAnalysisPage
from .self_analysis_storage import SelfAnalysisStorage
from .storage import DiaryStorage
from .thought_page import ThoughtPage
from .thought_storage import ThoughtStorage
from .work_page import WorkPage
from .work_storage import WorkStorage


class DiaryMainWindow(QMainWindow):
    def __init__(
        self,
        diary_storage: DiaryStorage,
        footprint_storage: FootprintStorage,
        book_storage: BookStorage,
        plan_storage: PlanStorage,
        lesson_storage: LessonStorage | None = None,
        self_analysis_storage: SelfAnalysisStorage | None = None,
        work_storage: WorkStorage | None = None,
        thought_storage: ThoughtStorage | None = None,
        resource_storage: ResourceStorage | None = None,
        observation_storage: ObservationStorage | None = None,
    ):
        super().__init__()
        self.diary_storage = diary_storage
        self.footprint_storage = footprint_storage
        self.book_storage = book_storage
        self.plan_storage = plan_storage
        self.lesson_storage = lesson_storage or LessonStorage(diary_storage.root_dir)
        self.self_analysis_storage = self_analysis_storage or SelfAnalysisStorage(diary_storage.root_dir)
        self.work_storage = work_storage or WorkStorage(diary_storage.root_dir)
        self.thought_storage = thought_storage or ThoughtStorage(diary_storage.root_dir)
        self.resource_storage = resource_storage or ResourceStorage(diary_storage.root_dir)
        self.observation_storage = observation_storage or ObservationStorage(diary_storage.root_dir)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("人生档案 Diary Desktop 3.0 - 双端闭环与深度整理版")
        self.resize(1260, 840)

        self.tabs = QTabWidget(self)
        self.overview_page = OverviewPage(self._create_overview_service(), self.tabs)
        self.diary_page = DiaryPage(self.diary_storage, self.footprint_storage, self.tabs)
        self.footprint_page = FootprintPage(self.footprint_storage, self.diary_storage, self.tabs)
        self.plan_page = PlanPage(self.plan_storage, self.tabs)
        self.lesson_page = LessonPage(self.lesson_storage, self.diary_storage, self.tabs)
        self.self_analysis_page = SelfAnalysisPage(
            self.self_analysis_storage,
            self.diary_storage,
            self.lesson_storage,
            self.tabs,
        )
        self.work_page = WorkPage(
            self.work_storage,
            self.diary_storage,
            self.self_analysis_storage,
            self.tabs,
        )
        self.thought_page = ThoughtPage(self.thought_storage, self.plan_storage, self.tabs)
        self.resource_page = ResourcePage(
            self.resource_storage,
            self.plan_storage,
            self.lesson_storage,
            self.tabs,
        )
        self.observation_page = ObservationPage(
            self.observation_storage,
            self.self_analysis_storage,
            self.tabs,
        )
        self.data_manager_page = DataManagerPage(self.diary_storage.root_dir, self.tabs)

        self.tabs.addTab(self.overview_page, "总览")
        self.tabs.addTab(self.diary_page, "日记")
        self.tabs.addTab(self.footprint_page, "足迹")
        self.tabs.addTab(self.work_page, "作品感悟")
        self.tabs.addTab(self.plan_page, "轻计划")
        self.tabs.addTab(self.lesson_page, "教训与反思")
        self.tabs.addTab(self.self_analysis_page, "自我分析")
        self.tabs.addTab(self.thought_page, "轻思考")
        self.tabs.addTab(self.resource_page, "轻资源")
        self.tabs.addTab(self.observation_page, "自我观察")
        self.tabs.addTab(self.data_manager_page, "数据管理")
        self.setCentralWidget(self.tabs)
        self._apply_style()
        self._previous_tab_index = self.tabs.currentIndex()

        self.diary_page.dirty_state_changed.connect(self._update_tab_titles)
        self.footprint_page.dirty_state_changed.connect(self._update_tab_titles)
        self.plan_page.dirty_state_changed.connect(self._update_tab_titles)
        self.lesson_page.dirty_state_changed.connect(self._update_tab_titles)
        self.self_analysis_page.dirty_state_changed.connect(self._update_tab_titles)
        self.work_page.dirty_state_changed.connect(self._update_tab_titles)
        self.thought_page.dirty_state_changed.connect(self._update_tab_titles)
        self.resource_page.dirty_state_changed.connect(self._update_tab_titles)
        self.observation_page.dirty_state_changed.connect(self._update_tab_titles)
        self.diary_page.show_footprints_requested.connect(self._open_footprints_for_date)
        self.footprint_page.open_diary_requested.connect(self._open_diary_for_date)
        self.lesson_page.open_diary_requested.connect(self._open_diary_from_lesson)
        self.self_analysis_page.open_diary_requested.connect(self._open_diary_from_self_analysis)
        self.self_analysis_page.open_lesson_requested.connect(self._open_lesson_from_self_analysis)
        self.work_page.open_diary_requested.connect(self._open_diary_from_work)
        self.work_page.open_self_analysis_requested.connect(self._open_self_analysis_from_work)
        self.thought_page.plan_created.connect(self._open_plan_from_related)
        self.resource_page.plan_created.connect(self._open_plan_from_related)
        self.resource_page.lesson_created.connect(self._open_lesson_from_self_analysis)
        self.observation_page.analysis_created.connect(self._open_self_analysis_from_work)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.overview_page.backup_requested.connect(self._backup_data)
        self.overview_page.restore_requested.connect(self._restore_data)
        self.overview_page.open_record_requested.connect(self._open_timeline_record)
        self.data_manager_page.backup_requested.connect(self._backup_data)
        self.data_manager_page.restore_requested.connect(self._restore_data)
        self.data_manager_page.import_mobile_requested.connect(self._import_mobile_zip)
        self.data_manager_page.export_desktop_requested.connect(self._export_desktop_zip)

        self.statusBar().showMessage(f"数据目录：{self.diary_storage.root_dir}", 6000)
        self._update_tab_titles()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        pages = [self.tabs.currentWidget()]
        for page in self._editable_pages():
            if page not in pages:
                pages.append(page)

        for page in pages:
            if hasattr(page, "maybe_finish_pending_changes") and not page.maybe_finish_pending_changes():
                event.ignore()
                return

        event.accept()

    def _on_tab_changed(self, current_index: int) -> None:
        previous_index = getattr(self, "_previous_tab_index", current_index)
        if previous_index != current_index:
            previous_page = self.tabs.widget(previous_index)
            if (
                hasattr(previous_page, "maybe_finish_pending_changes")
                and not previous_page.maybe_finish_pending_changes()
            ):
                previous_blocked = self.tabs.blockSignals(True)
                self.tabs.setCurrentIndex(previous_index)
                self.tabs.blockSignals(previous_blocked)
                return

        current_page = self.tabs.widget(current_index)
        if current_page is self.overview_page:
            self.overview_page.refresh_overview()
        self._previous_tab_index = current_index

    def _update_tab_titles(self) -> None:
        diary_title = "日记 *" if self.diary_page.has_unsaved_changes() else "日记"
        footprint_title = "足迹 *" if self.footprint_page.has_unsaved_changes() else "足迹"
        work_title = "作品感悟 *" if self.work_page.has_unsaved_changes() else "作品感悟"
        plan_title = "轻计划 *" if self.plan_page.has_unsaved_changes() else "轻计划"
        lesson_title = "教训与反思 *" if self.lesson_page.has_unsaved_changes() else "教训与反思"
        self_analysis_title = "自我分析 *" if self.self_analysis_page.has_unsaved_changes() else "自我分析"
        thought_title = "轻思考 *" if self.thought_page.has_unsaved_changes() else "轻思考"
        resource_title = "轻资源 *" if self.resource_page.has_unsaved_changes() else "轻资源"
        observation_title = "自我观察 *" if self.observation_page.has_unsaved_changes() else "自我观察"
        self.tabs.setTabText(0, "总览")
        self.tabs.setTabText(1, diary_title)
        self.tabs.setTabText(2, footprint_title)
        self.tabs.setTabText(3, work_title)
        self.tabs.setTabText(4, plan_title)
        self.tabs.setTabText(5, lesson_title)
        self.tabs.setTabText(6, self_analysis_title)
        self.tabs.setTabText(7, thought_title)
        self.tabs.setTabText(8, resource_title)
        self.tabs.setTabText(9, observation_title)
        self.tabs.setTabText(10, "数据管理")

    def _backup_data(self) -> None:
        if not self._finish_all_pending_changes():
            return
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "选择备份文件保存位置",
            str((self.diary_storage.root_dir.parent / "backups").resolve()),
        )
        if not output_dir:
            return
        try:
            backup_path = create_backup(self.diary_storage.root_dir, output_dir, APP_VERSION)
        except Exception as exc:
            QMessageBox.critical(self, "备份失败", f"备份数据时出错：\n{exc}")
            return
        QMessageBox.information(self, "备份完成", f"备份文件已生成：\n\n{backup_path}")
        self.statusBar().showMessage("数据备份完成。", 5000)

    def _restore_data(self) -> None:
        if not self._finish_all_pending_changes():
            return
        zip_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择备份包",
            str((self.diary_storage.root_dir.parent / "backups").resolve()),
            "Zip Backup (*.zip)",
        )
        if not zip_path:
            return

        valid, message = validate_backup(zip_path)
        if not valid:
            QMessageBox.warning(self, "备份包无效", message)
            return

        reply = QMessageBox.question(
            self,
            "恢复确认",
            "恢复会用备份包中的 Diary/ 替换当前数据。恢复前会自动备份当前数据，是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            safety_backup_path = restore_backup(
                zip_path,
                self.diary_storage.root_dir,
                self.diary_storage.root_dir.parent / "backups",
                APP_VERSION,
            )
        except Exception as exc:
            QMessageBox.critical(self, "恢复失败", f"恢复备份时出错：\n{exc}")
            return

        self._reload_data_after_restore()
        QMessageBox.information(
            self,
            "恢复完成",
            "恢复完成，已自动备份恢复前的数据：\n\n"
            f"{safety_backup_path}",
        )
        self.statusBar().showMessage("备份恢复完成。", 5000)

    def _import_mobile_zip(self) -> None:
        if not self._finish_all_pending_changes():
            return
        zip_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 LifeDiary 手机版 ZIP 数据包",
            str((self.diary_storage.root_dir.parent / "backups").resolve()),
            "LifeDiary ZIP (*.zip)",
        )
        if not zip_path:
            return

        valid, message, manifest = validate_mobile_backup(zip_path)
        if not valid:
            QMessageBox.warning(self, "数据包无效", message)
            return

        modules = manifest.get("modules", [])
        module_text = "、".join(str(item.get("key", item)) for item in modules) if isinstance(modules, list) else str(modules)
        reply = QMessageBox.question(
            self,
            "导入确认",
            "导入前会自动备份当前电脑端 data/Diary/，随后按 id 合并手机版数据，不会简单覆盖整个目录。\n\n"
            f"备份时间：{manifest.get('backup_time') or manifest.get('created_at') or '未知'}\n"
            f"模块：{module_text or '未声明'}\n\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            safety_backup_path, stats, manifest = import_mobile_backup(
                zip_path,
                self.diary_storage.root_dir,
                self.diary_storage.root_dir.parent / "backups",
                APP_VERSION,
            )
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", f"导入手机版数据包时出错，当前数据已尽量恢复到导入前状态：\n{exc}")
            return

        self._reload_data_after_restore()
        QMessageBox.information(
            self,
            "导入完成",
            f"{format_import_stats(stats, manifest)}\n\n导入前自动备份：\n{safety_backup_path}",
        )
        self.statusBar().showMessage("手机版数据导入完成。", 5000)

    def _export_desktop_zip(self) -> None:
        self._backup_data()

    def _finish_all_pending_changes(self) -> bool:
        pages = [self.tabs.currentWidget()]
        for page in self._editable_pages():
            if page not in pages:
                pages.append(page)
        for page in pages:
            if hasattr(page, "maybe_finish_pending_changes") and not page.maybe_finish_pending_changes():
                return False
        return True

    def _editable_pages(self) -> tuple:
        return (
            self.diary_page,
            self.footprint_page,
            self.plan_page,
            self.lesson_page,
            self.self_analysis_page,
            self.work_page,
            self.thought_page,
            self.resource_page,
            self.observation_page,
        )

    def _create_overview_service(self) -> OverviewService:
        return OverviewService(
            self.diary_storage,
            self.footprint_storage,
            self.book_storage,
            self.plan_storage,
            self.lesson_storage,
            self.self_analysis_storage,
            self.work_storage,
            self.thought_storage,
            self.resource_storage,
            self.observation_storage,
        )

    def _reload_data_after_restore(self) -> None:
        root_dir = self.diary_storage.root_dir
        self.diary_storage = DiaryStorage(root_dir)
        self.footprint_storage = FootprintStorage(root_dir)
        self.book_storage = BookStorage(root_dir)
        self.plan_storage = PlanStorage(root_dir)
        self.lesson_storage = LessonStorage(root_dir)
        self.self_analysis_storage = SelfAnalysisStorage(root_dir)
        self.work_storage = WorkStorage(root_dir)
        self.thought_storage = ThoughtStorage(root_dir)
        self.resource_storage = ResourceStorage(root_dir)
        self.observation_storage = ObservationStorage(root_dir)

        self.diary_page.storage = self.diary_storage
        self.diary_page.footprint_storage = self.footprint_storage
        self.footprint_page.storage = self.footprint_storage
        self.footprint_page.diary_storage = self.diary_storage
        self.plan_page.storage = self.plan_storage
        self.lesson_page.storage = self.lesson_storage
        self.lesson_page.diary_storage = self.diary_storage
        self.self_analysis_page.storage = self.self_analysis_storage
        self.self_analysis_page.diary_storage = self.diary_storage
        self.self_analysis_page.lesson_storage = self.lesson_storage
        self.work_page.storage = self.work_storage
        self.work_page.diary_storage = self.diary_storage
        self.work_page.self_analysis_storage = self.self_analysis_storage
        self.thought_page.storage = self.thought_storage
        self.thought_page.plan_storage = self.plan_storage
        self.resource_page.storage = self.resource_storage
        self.resource_page.plan_storage = self.plan_storage
        self.resource_page.lesson_storage = self.lesson_storage
        self.observation_page.storage = self.observation_storage
        self.observation_page.self_analysis_storage = self.self_analysis_storage
        self.data_manager_page.set_data_root(root_dir)
        self.overview_page.service = self._create_overview_service()

        self._reset_page_after_restore(self.diary_page, "current_entry", "image_items", "refresh_list", "entry_list", "new_entry")
        self._reset_page_after_restore(
            self.footprint_page,
            "current_place",
            "place_image_items",
            "refresh_place_list",
            "place_list",
            "new_place",
            extra_resets=[("current_visit_id", None), ("visit_image_items", {})],
        )
        self._reset_page_after_restore(self.plan_page, "current_plan", None, "refresh_list", "plan_list", "new_plan")
        self._reset_page_after_restore(self.lesson_page, "current_lesson", "image_items", "refresh_lesson_list", "lesson_list", "new_lesson")
        self._reset_page_after_restore(
            self.self_analysis_page,
            "current_analysis",
            "image_items",
            "refresh_analysis_list",
            "analysis_list",
            "new_analysis",
        )
        self._reset_page_after_restore(self.work_page, "current_work", "image_items", "refresh_work_list", "work_list", "new_work")
        self._reset_page_after_restore(self.thought_page, "current_thought", None, "refresh_thought_list", "thought_list", "new_thought")
        self._reset_page_after_restore(self.resource_page, "current_resource", None, "refresh_resource_list", "resource_list", "new_resource")
        self._reset_page_after_restore(
            self.observation_page,
            "current_observation",
            None,
            "refresh_observation_list",
            "observation_list",
            "new_observation",
        )
        self.overview_page.refresh_overview()
        self._update_tab_titles()

    def _reset_page_after_restore(
        self,
        page,
        current_attr: str,
        image_attr: str | None,
        refresh_method: str,
        list_attr: str,
        new_method: str,
        extra_resets: list[tuple[str, object]] | None = None,
    ) -> None:
        if hasattr(page, "_suspend_auto_save"):
            page._suspend_auto_save()
        setattr(page, current_attr, None)
        if image_attr:
            setattr(page, image_attr, [])
        for attr, value in extra_resets or []:
            setattr(page, attr, value)
        if hasattr(page, "_set_dirty"):
            page._set_dirty(False)
        getattr(page, refresh_method)()
        list_widget = getattr(page, list_attr)
        if list_widget.count() > 0 and list_widget.item(0).data(Qt.ItemDataRole.UserRole):
            list_widget.setCurrentRow(0)
        else:
            getattr(page, new_method)()
        if hasattr(page, "_resume_auto_save"):
            page._resume_auto_save()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f6f7f4;
                color: #202722;
                font-family: Microsoft YaHei, Segoe UI, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #d8ddd4;
                background: #fbfcfa;
            }
            QTabBar::tab {
                background: #e7ece4;
                border: 1px solid #d4dacd;
                padding: 8px 18px;
                margin-right: 3px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
                color: #24452e;
                font-weight: 600;
            }
            QLineEdit, QTextEdit, QDateEdit, QComboBox, QListWidget {
                background: #ffffff;
                border: 1px solid #cfd7ca;
                border-radius: 6px;
                padding: 6px;
                selection-background-color: #8fbf8d;
            }
            QGroupBox {
                border: 1px solid #d6ddd2;
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px 10px 10px 10px;
                background: #fbfcfa;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #315c3c;
            }
            QPushButton {
                background: #315c3c;
                color: #ffffff;
                border: 1px solid #284c32;
                border-radius: 6px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background: #3f704c;
            }
            QPushButton:disabled {
                background: #c8d0c3;
                border-color: #bdc6b8;
                color: #eef2eb;
            }
            QListWidget::item {
                border-radius: 6px;
                padding: 7px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: #dcebd8;
                color: #1d3a26;
            }
            """
        )

    def _open_footprints_for_date(self, target_date: str) -> None:
        result = self.footprint_page.open_first_place_for_date(target_date)
        if result is True:
            self.tabs.setCurrentWidget(self.footprint_page)
            return
        if result is False:
            QMessageBox.information(self, "当天没有足迹", f"{target_date} 还没有足迹记录。")

    def _open_diary_for_date(self, target_date: str) -> None:
        result = self.diary_page.open_first_entry_for_date(target_date)
        if result is True:
            self.tabs.setCurrentWidget(self.diary_page)
            return
        if result is False:
            QMessageBox.information(self, "当天没有日记", f"{target_date} 还没有日记。")

    def _open_diary_from_lesson(self, entry_id: str, target_date: str) -> None:
        self._open_diary_from_relation(entry_id, target_date)

    def _open_diary_from_self_analysis(self, entry_id: str, target_date: str) -> None:
        self._open_diary_from_relation(entry_id, target_date)

    def _open_lesson_from_self_analysis(self, lesson_id: str) -> None:
        if not lesson_id:
            return
        self.lesson_page._open_lesson_by_id(lesson_id)
        self.tabs.setCurrentWidget(self.lesson_page)

    def _open_diary_from_work(self, entry_id: str, target_date: str) -> None:
        self._open_diary_from_relation(entry_id, target_date)

    def _open_self_analysis_from_work(self, analysis_id: str) -> None:
        if not analysis_id:
            return
        self.self_analysis_page.open_analysis_by_id(analysis_id)
        self.tabs.setCurrentWidget(self.self_analysis_page)

    def _open_plan_from_related(self, plan_id: str) -> None:
        if not plan_id:
            return
        if hasattr(self.plan_page, "open_plan_by_id"):
            self.plan_page.open_plan_by_id(plan_id)
        self.tabs.setCurrentWidget(self.plan_page)

    def _open_timeline_record(self, source_module: str, record_id: str) -> None:
        if source_module == "entries":
            self.diary_page.open_entry_by_id(record_id)
            self.tabs.setCurrentWidget(self.diary_page)
        elif source_module == "footprints":
            place_id, _sep, visit_id = record_id.partition(":")
            self.footprint_page._open_place_by_id(place_id, select_visit_id=visit_id or None)
            self.tabs.setCurrentWidget(self.footprint_page)
        elif source_module == "books":
            self.work_page.open_work_by_id(record_id)
            self.tabs.setCurrentWidget(self.work_page)
        elif source_module == "works":
            self.work_page.open_work_by_id(record_id)
            self.tabs.setCurrentWidget(self.work_page)
        elif source_module == "plans":
            self._open_plan_from_related(record_id)
        elif source_module == "lessons":
            self._open_lesson_from_self_analysis(record_id)
        elif source_module == "self_analysis":
            self._open_self_analysis_from_work(record_id)
        elif source_module == "thoughts":
            self.thought_page.open_thought_by_id(record_id)
            self.tabs.setCurrentWidget(self.thought_page)
        elif source_module == "resources":
            self.resource_page.open_resource_by_id(record_id)
            self.tabs.setCurrentWidget(self.resource_page)
        elif source_module == "observations":
            self.observation_page.open_observation_by_id(record_id)
            self.tabs.setCurrentWidget(self.observation_page)

    def _open_diary_from_relation(self, entry_id: str, target_date: str) -> None:
        if entry_id:
            result = self.diary_page.open_entry_by_id(entry_id)
            if result is True:
                self.tabs.setCurrentWidget(self.diary_page)
                return
            if result is None:
                return

        result = self.diary_page.open_first_entry_for_date(target_date)
        if result is True:
            self.tabs.setCurrentWidget(self.diary_page)
            return
        if result is False:
            QMessageBox.information(self, "关联日记不存在", f"找不到这条关联对应的日记：{target_date}")
