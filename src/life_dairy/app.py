from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from . import __version__
from .book_storage import BookStorage
from .footprint_storage import FootprintStorage
from .info_memo_storage import InfoMemoStorage
from .lesson_storage import LessonStorage
from .logger import get_logger, setup_logger
from .main_window import DiaryMainWindow
from .observation_storage import ObservationStorage
from .plan_storage import PlanStorage
from .resource_storage import ResourceStorage
from .self_analysis_storage import SelfAnalysisStorage
from .storage import DiaryStorage, default_data_dir
from .thought_storage import ThoughtStorage
from .work_storage import WorkStorage


def main() -> int:
    data_dir = default_data_dir()
    log_dir = data_dir / 'logs'
    setup_logger('life_dairy', log_dir)
    logger = get_logger('life_dairy')
    logger.info('=' * 60)
    logger.info(f"人生档案 Diary v{__version__} 启动，数据目录: {data_dir}")

    def _unhandled_excepthook(exc_type, exc_value, exc_tb) -> None:
        logger.critical("未处理的异常", exc_info=(exc_type, exc_value, exc_tb))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _unhandled_excepthook
    app = QApplication(sys.argv)
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
        InfoMemoStorage(data_dir),
    )
    window.show()
    return app.exec()
