from __future__ import annotations

import sys
import webbrowser

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView

from data_api import APP_TITLE, FRONTEND_DIST
from server import start_server


class MainWindow(QMainWindow):
    def __init__(self, url: str):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1320, 860)
        view = QWebEngineView(self)
        view.load(QUrl(url))
        self.setCentralWidget(view)


def main() -> int:
    server = start_server()
    url = f"http://127.0.0.1:{server.server_port}/"
    app = QApplication(sys.argv)
    window = MainWindow(url)
    window.show()
    result = app.exec()
    server.shutdown()
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        fallback = FRONTEND_DIST / "index.html"
        if fallback.exists():
            webbrowser.open(fallback.as_uri())
        raise
