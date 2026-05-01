from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .book_storage import BookStorage
from .footprint_storage import FootprintStorage
from .lesson_storage import LessonStorage
from .main_window import DiaryMainWindow
from .plan_storage import PlanStorage
from .self_analysis_storage import SelfAnalysisStorage
from .storage import DiaryStorage, default_data_dir


def main() -> int:
    app = QApplication(sys.argv)
    data_dir = default_data_dir()
    window = DiaryMainWindow(
        DiaryStorage(data_dir),
        FootprintStorage(data_dir),
        BookStorage(data_dir),
        PlanStorage(data_dir),
        LessonStorage(data_dir),
        SelfAnalysisStorage(data_dir),
    )
    window.show()
    return app.exec()
