from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QTabWidget

from .backup_service import APP_VERSION, create_backup, restore_backup, validate_backup
from .book_page import BookPage
from .book_storage import BookStorage
from .diary_page import DiaryPage
from .footprint_page import FootprintPage
from .footprint_storage import FootprintStorage
from .lesson_page import LessonPage
from .lesson_storage import LessonStorage
from .overview import OverviewService
from .overview_page import OverviewPage
from .plan_page import PlanPage
from .plan_storage import PlanStorage
from .self_analysis_page import SelfAnalysisPage
from .self_analysis_storage import SelfAnalysisStorage
from .storage import DiaryStorage


class DiaryMainWindow(QMainWindow):
    def __init__(
        self,
        diary_storage: DiaryStorage,
        footprint_storage: FootprintStorage,
        book_storage: BookStorage,
        plan_storage: PlanStorage,
        lesson_storage: LessonStorage | None = None,
        self_analysis_storage: SelfAnalysisStorage | None = None,
    ):
        super().__init__()
        self.diary_storage = diary_storage
        self.footprint_storage = footprint_storage
        self.book_storage = book_storage
        self.plan_storage = plan_storage
        self.lesson_storage = lesson_storage or LessonStorage(diary_storage.root_dir)
        self.self_analysis_storage = self_analysis_storage or SelfAnalysisStorage(diary_storage.root_dir)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("人生档案 Diary - 总览、日记、足迹、读书与反思")
        self.resize(1260, 840)

        self.tabs = QTabWidget(self)
        self.overview_page = OverviewPage(
            OverviewService(
                self.diary_storage,
                self.footprint_storage,
                self.book_storage,
                self.plan_storage,
                self.lesson_storage,
            ),
            self.tabs,
        )
        self.diary_page = DiaryPage(self.diary_storage, self.footprint_storage, self.tabs)
        self.footprint_page = FootprintPage(self.footprint_storage, self.diary_storage, self.tabs)
        self.book_page = BookPage(self.book_storage, self.diary_storage, self.tabs)
        self.plan_page = PlanPage(self.plan_storage, self.tabs)
        self.lesson_page = LessonPage(self.lesson_storage, self.diary_storage, self.tabs)
        self.self_analysis_page = SelfAnalysisPage(
            self.self_analysis_storage,
            self.diary_storage,
            self.lesson_storage,
            self.tabs,
        )

        self.tabs.addTab(self.overview_page, "总览")
        self.tabs.addTab(self.diary_page, "日记")
        self.tabs.addTab(self.footprint_page, "足迹")
        self.tabs.addTab(self.book_page, "读书")
        self.tabs.addTab(self.plan_page, "轻计划")
        self.tabs.addTab(self.lesson_page, "教训与反思")
        self.tabs.addTab(self.self_analysis_page, "自我分析")
        self.setCentralWidget(self.tabs)
        self._apply_style()
        self._previous_tab_index = self.tabs.currentIndex()

        self.diary_page.dirty_state_changed.connect(self._update_tab_titles)
        self.footprint_page.dirty_state_changed.connect(self._update_tab_titles)
        self.book_page.dirty_state_changed.connect(self._update_tab_titles)
        self.plan_page.dirty_state_changed.connect(self._update_tab_titles)
        self.lesson_page.dirty_state_changed.connect(self._update_tab_titles)
        self.self_analysis_page.dirty_state_changed.connect(self._update_tab_titles)
        self.diary_page.show_footprints_requested.connect(self._open_footprints_for_date)
        self.footprint_page.open_diary_requested.connect(self._open_diary_for_date)
        self.book_page.open_diary_requested.connect(self._open_diary_from_book)
        self.lesson_page.open_diary_requested.connect(self._open_diary_from_lesson)
        self.self_analysis_page.open_diary_requested.connect(self._open_diary_from_self_analysis)
        self.self_analysis_page.open_lesson_requested.connect(self._open_lesson_from_self_analysis)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.overview_page.backup_requested.connect(self._backup_data)
        self.overview_page.restore_requested.connect(self._restore_data)

        self.statusBar().showMessage(f"数据目录：{self.diary_storage.root_dir}", 6000)
        self._update_tab_titles()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        pages = [self.tabs.currentWidget()]
        for page in (
            self.diary_page,
            self.footprint_page,
            self.book_page,
            self.plan_page,
            self.lesson_page,
            self.self_analysis_page,
        ):
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
        book_title = "读书 *" if self.book_page.has_unsaved_changes() else "读书"
        plan_title = "轻计划 *" if self.plan_page.has_unsaved_changes() else "轻计划"
        lesson_title = "教训与反思 *" if self.lesson_page.has_unsaved_changes() else "教训与反思"
        self_analysis_title = "自我分析 *" if self.self_analysis_page.has_unsaved_changes() else "自我分析"
        self.tabs.setTabText(0, "总览")
        self.tabs.setTabText(1, diary_title)
        self.tabs.setTabText(2, footprint_title)
        self.tabs.setTabText(3, book_title)
        self.tabs.setTabText(4, plan_title)
        self.tabs.setTabText(5, lesson_title)
        self.tabs.setTabText(6, self_analysis_title)

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

    def _finish_all_pending_changes(self) -> bool:
        pages = [self.tabs.currentWidget()]
        for page in (
            self.diary_page,
            self.footprint_page,
            self.book_page,
            self.plan_page,
            self.lesson_page,
            self.self_analysis_page,
        ):
            if page not in pages:
                pages.append(page)
        for page in pages:
            if hasattr(page, "maybe_finish_pending_changes") and not page.maybe_finish_pending_changes():
                return False
        return True

    def _reload_data_after_restore(self) -> None:
        root_dir = self.diary_storage.root_dir
        self.diary_storage = DiaryStorage(root_dir)
        self.footprint_storage = FootprintStorage(root_dir)
        self.book_storage = BookStorage(root_dir)
        self.plan_storage = PlanStorage(root_dir)
        self.lesson_storage = LessonStorage(root_dir)
        self.self_analysis_storage = SelfAnalysisStorage(root_dir)

        self.diary_page.storage = self.diary_storage
        self.diary_page.footprint_storage = self.footprint_storage
        self.footprint_page.storage = self.footprint_storage
        self.footprint_page.diary_storage = self.diary_storage
        self.book_page.storage = self.book_storage
        self.book_page.diary_storage = self.diary_storage
        self.plan_page.storage = self.plan_storage
        self.lesson_page.storage = self.lesson_storage
        self.lesson_page.diary_storage = self.diary_storage
        self.self_analysis_page.storage = self.self_analysis_storage
        self.self_analysis_page.diary_storage = self.diary_storage
        self.self_analysis_page.lesson_storage = self.lesson_storage
        self.overview_page.service = OverviewService(
            self.diary_storage,
            self.footprint_storage,
            self.book_storage,
            self.plan_storage,
            self.lesson_storage,
        )

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
        self._reset_page_after_restore(self.book_page, "current_book", "image_items", "refresh_book_list", "book_list", "new_book")
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
        if list_widget.count() > 0:
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

    def _open_diary_from_book(self, entry_id: str, target_date: str) -> None:
        self._open_diary_from_relation(entry_id, target_date)

    def _open_diary_from_lesson(self, entry_id: str, target_date: str) -> None:
        self._open_diary_from_relation(entry_id, target_date)

    def _open_diary_from_self_analysis(self, entry_id: str, target_date: str) -> None:
        self._open_diary_from_relation(entry_id, target_date)

    def _open_lesson_from_self_analysis(self, lesson_id: str) -> None:
        if not lesson_id:
            return
        self.lesson_page._open_lesson_by_id(lesson_id)
        self.tabs.setCurrentWidget(self.lesson_page)

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
