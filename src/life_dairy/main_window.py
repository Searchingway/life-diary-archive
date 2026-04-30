from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

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
from .storage import DiaryStorage


class DiaryMainWindow(QMainWindow):
    def __init__(
        self,
        diary_storage: DiaryStorage,
        footprint_storage: FootprintStorage,
        book_storage: BookStorage,
        plan_storage: PlanStorage,
        lesson_storage: LessonStorage | None = None,
    ):
        super().__init__()
        self.diary_storage = diary_storage
        self.footprint_storage = footprint_storage
        self.book_storage = book_storage
        self.plan_storage = plan_storage
        self.lesson_storage = lesson_storage or LessonStorage(diary_storage.root_dir)
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

        self.tabs.addTab(self.overview_page, "总览")
        self.tabs.addTab(self.diary_page, "日记")
        self.tabs.addTab(self.footprint_page, "足迹")
        self.tabs.addTab(self.book_page, "读书")
        self.tabs.addTab(self.plan_page, "轻计划")
        self.tabs.addTab(self.lesson_page, "教训与反思")
        self.setCentralWidget(self.tabs)
        self._apply_style()
        self._previous_tab_index = self.tabs.currentIndex()

        self.diary_page.dirty_state_changed.connect(self._update_tab_titles)
        self.footprint_page.dirty_state_changed.connect(self._update_tab_titles)
        self.book_page.dirty_state_changed.connect(self._update_tab_titles)
        self.plan_page.dirty_state_changed.connect(self._update_tab_titles)
        self.lesson_page.dirty_state_changed.connect(self._update_tab_titles)
        self.diary_page.show_footprints_requested.connect(self._open_footprints_for_date)
        self.footprint_page.open_diary_requested.connect(self._open_diary_for_date)
        self.book_page.open_diary_requested.connect(self._open_diary_from_book)
        self.lesson_page.open_diary_requested.connect(self._open_diary_from_lesson)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.statusBar().showMessage(f"数据目录：{self.diary_storage.root_dir}", 6000)
        self._update_tab_titles()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        pages = [self.tabs.currentWidget()]
        for page in (self.diary_page, self.footprint_page, self.book_page, self.plan_page, self.lesson_page):
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
        self.tabs.setTabText(0, "总览")
        self.tabs.setTabText(1, diary_title)
        self.tabs.setTabText(2, footprint_title)
        self.tabs.setTabText(3, book_title)
        self.tabs.setTabText(4, plan_title)
        self.tabs.setTabText(5, lesson_title)

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
