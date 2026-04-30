from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox


class AutoSaveMixin:
    def _init_auto_save(self, interval_ms: int = 3000) -> None:
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.setInterval(interval_ms)
        self._auto_save_timer.timeout.connect(self.perform_auto_save)
        self._auto_save_suspended = False

    def _on_dirty_state_changed_for_autosave(self, is_dirty: bool) -> None:
        if self._auto_save_suspended:
            return
        if not hasattr(self, "_auto_save_timer"):
            return
        if is_dirty:
            self._show_auto_save_status("有未保存修改")
            if self._auto_save_has_meaningful_content():
                self._auto_save_timer.start()
            else:
                self._auto_save_timer.stop()
            return
        self._auto_save_timer.stop()
        self._show_auto_save_status("已保存")

    def _suspend_auto_save(self) -> None:
        self._auto_save_suspended = True
        if hasattr(self, "_auto_save_timer"):
            self._auto_save_timer.stop()

    def _resume_auto_save(self) -> None:
        self._auto_save_suspended = False

    def perform_auto_save(self) -> bool:
        if not getattr(self, "is_dirty", False):
            return True
        if not self._auto_save_has_meaningful_content():
            return True

        if hasattr(self, "_auto_save_timer"):
            self._auto_save_timer.stop()
        self._show_auto_save_status("自动保存中")

        try:
            saved = bool(self._auto_save_now())
        except Exception:
            saved = False

        if saved and not getattr(self, "is_dirty", False):
            self._show_auto_save_status("已自动保存")
            return True

        self._show_auto_save_status("自动保存失败")
        return False

    def maybe_finish_pending_changes(self) -> bool:
        if not getattr(self, "is_dirty", False):
            return True
        if self.perform_auto_save():
            return True

        QMessageBox.warning(
            self,
            "自动保存失败",
            "当前页面仍有未保存内容，请手动保存成功后再继续。",
        )
        return False

    def _auto_save_now(self) -> bool:
        raise NotImplementedError

    def _auto_save_has_meaningful_content(self) -> bool:
        return True

    def _show_auto_save_status(self, message: str) -> None:
        if hasattr(self, "_show_status"):
            self._show_status(message, 3000)
