from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFrame,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QWidget,
)


def make_scroll_area(widget: QWidget) -> QScrollArea:
    scroll_area = QScrollArea(widget.parent())
    scroll_area.setWidgetResizable(True)
    scroll_area.setFrameShape(QFrame.Shape.NoFrame)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setWidget(widget)
    return scroll_area


IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"})


def _extract_image_paths_from_mime(mime) -> list[Path]:
    """Extract image file paths from various mime data sources.

    Supports:
    - urls (file manager / standard drag)
    - text (WeChat may pass paths as plain text)
    - html (WeChat may embed file:/// paths in HTML fragments)
    """
    paths: list[Path] = []

    # 1. Standard URL-based files (file manager, most apps)
    if mime.hasUrls():
        for url in mime.urls():
            if url.isLocalFile():
                paths.append(Path(url.toLocalFile()))

    # 2. Plain text lines (WeChat on Windows often passes paths as text)
    if not paths and mime.hasText():
        text = mime.text().strip()
        for line in text.splitlines():
            line = line.strip().strip("\"'“”")
            candidate = Path(line)
            if candidate.exists():
                paths.append(candidate)

    # 3. HTML with file:// URIs (another WeChat mechanism)
    if not paths and mime.hasHtml():
        html = mime.html()
        import re

        for m in re.finditer(r"file:///([^\s\"<>'“”]+)", html):
            candidate = Path(m.group(1))
            if candidate.exists():
                paths.append(candidate)

    # Filter to image files only
    result = [p for p in paths if p.suffix.lower() in IMAGE_EXTENSIONS]
    seen: set[str] = set()
    unique = []
    for p in result:
        key = str(p.resolve()).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


class DropTargetImageList(QListWidget):
    """QListWidget that accepts drag-and-drop of image files.

    Emits files_dropped(list[Path]) when valid image files are dropped.
    """

    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls() or mime.hasText() or mime.hasHtml():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDropEvent) -> None:
        if event.mimeData().hasUrls() or event.mimeData().hasText() or event.mimeData().hasHtml():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = _extract_image_paths_from_mime(event.mimeData())
        if not paths:
            QMessageBox.information(
                self,
                "不支持的格式",
                "拖入的文件不是支持的图片格式。\n\n支持的格式：jpg、jpeg、png、webp、bmp",
            )
            super().dropEvent(event)
            return

        self.files_dropped.emit(paths)
        event.acceptProposedAction()


def add_image_reorder_buttons(
    layout,
    image_list,
    image_items: list,
    on_reorder: Callable[[], None],
):
    """Add standard up/down reorder buttons for an image list.

    Args:
        layout: The layout to add buttons to.
        image_list: The QListWidget containing image items.
        image_items: The backing list of image draft objects (swapped in-place).
        on_reorder: Called after a successful swap. Should refresh the list
                    display and mark the page as dirty.
    """
    up_btn = QPushButton("上移")
    down_btn = QPushButton("下移")

    def do_move_up():
        row = image_list.currentRow()
        if row <= 0:
            return
        image_items[row], image_items[row - 1] = image_items[row - 1], image_items[row]
        on_reorder()
        image_list.setCurrentRow(row - 1)

    def do_move_down():
        row = image_list.currentRow()
        if row < 0 or row >= len(image_items) - 1:
            return
        image_items[row], image_items[row + 1] = image_items[row + 1], image_items[row]
        on_reorder()
        image_list.setCurrentRow(row + 1)

    up_btn.clicked.connect(do_move_up)
    down_btn.clicked.connect(do_move_down)
    up_btn.setEnabled(False)
    down_btn.setEnabled(False)

    def _update_buttons(*_args):
        row = image_list.currentRow()
        up_btn.setEnabled(row > 0)
        down_btn.setEnabled(0 <= row < len(image_items) - 1)

    image_list.currentRowChanged.connect(_update_buttons)
    image_list.currentItemChanged.connect(_update_buttons)

    layout.addWidget(up_btn)
    layout.addWidget(down_btn)
