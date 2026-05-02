from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .book_storage import BookStorage
from .footprint_storage import FootprintStorage
from .lesson_storage import LessonStorage
from .main_window import DiaryMainWindow
from .observation_storage import ObservationStorage
from .plan_storage import PlanStorage
from .resource_storage import ResourceStorage
from .self_analysis_storage import SelfAnalysisStorage
from .storage import DiaryStorage, default_data_dir
from .thought_storage import ThoughtStorage
from .work_storage import WorkStorage


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
        WorkStorage(data_dir),
        ThoughtStorage(data_dir),
        ResourceStorage(data_dir),
        ObservationStorage(data_dir),
    )
    window.show()
    return app.exec()
