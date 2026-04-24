from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from .book_page import BookPage
from .book_storage import BookStorage
from .diary_page import DiaryPage
from .footprint_page import FootprintPage
from .footprint_storage import FootprintStorage
from .storage import DiaryStorage


class DiaryMainWindow(QMainWindow):
    def __init__(
        self,
        diary_storage: DiaryStorage,
        footprint_storage: FootprintStorage,
        book_storage: BookStorage,
    ):
        super().__init__()
        self.diary_storage = diary_storage
        self.footprint_storage = footprint_storage
        self.book_storage = book_storage
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("人生档案 Diary - 日记、足迹与读书")
        self.resize(1260, 840)

        self.tabs = QTabWidget(self)
        self.diary_page = DiaryPage(self.diary_storage, self.footprint_storage, self.tabs)
        self.footprint_page = FootprintPage(self.footprint_storage, self.diary_storage, self.tabs)
        self.book_page = BookPage(self.book_storage, self.diary_storage, self.tabs)

        self.tabs.addTab(self.diary_page, "日记")
        self.tabs.addTab(self.footprint_page, "足迹")
        self.tabs.addTab(self.book_page, "读书")
        self.setCentralWidget(self.tabs)

        self.diary_page.dirty_state_changed.connect(self._update_tab_titles)
        self.footprint_page.dirty_state_changed.connect(self._update_tab_titles)
        self.book_page.dirty_state_changed.connect(self._update_tab_titles)
        self.diary_page.show_footprints_requested.connect(self._open_footprints_for_date)
        self.footprint_page.open_diary_requested.connect(self._open_diary_for_date)
        self.book_page.open_diary_requested.connect(self._open_diary_from_book)

        self.statusBar().showMessage(f"数据目录：{self.diary_storage.root_dir}", 6000)
        self._update_tab_titles()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        pages = [self.tabs.currentWidget()]
        for page in (self.diary_page, self.footprint_page, self.book_page):
            if page not in pages:
                pages.append(page)

        for page in pages:
            if hasattr(page, "maybe_finish_pending_changes") and not page.maybe_finish_pending_changes():
                event.ignore()
                return

        event.accept()

    def _update_tab_titles(self) -> None:
        diary_title = "日记 *" if self.diary_page.has_unsaved_changes() else "日记"
        footprint_title = "足迹 *" if self.footprint_page.has_unsaved_changes() else "足迹"
        book_title = "读书 *" if self.book_page.has_unsaved_changes() else "读书"
        self.tabs.setTabText(0, diary_title)
        self.tabs.setTabText(1, footprint_title)
        self.tabs.setTabText(2, book_title)

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
