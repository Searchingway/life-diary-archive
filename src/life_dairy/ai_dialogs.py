from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .ai_service import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    AISettings,
    load_ai_settings,
    save_ai_settings,
    test_ai_connection,
)
from .logger import get_logger

logger = get_logger("ai_dialogs")


class AISettingsDialog(QDialog):
    def __init__(self, data_root: Path | str, parent: QWidget | None = None):
        super().__init__(parent)
        self.data_root = Path(data_root)
        self.setWindowTitle("AI 设置")
        self.setMinimumWidth(500)
        self._build_ui()
        self._load_settings()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("sk-...")

        self.base_url_input = QLineEdit(self)
        self.base_url_input.setPlaceholderText(DEFAULT_BASE_URL)

        self.model_input = QLineEdit(self)
        self.model_input.setPlaceholderText(DEFAULT_MODEL)

        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setValue(DEFAULT_TIMEOUT)
        self.timeout_spin.setSuffix(" 秒")

        self.enabled_check = QCheckBox("启用 AI 功能", self)

        form.addRow("API Key", self.api_key_input)
        form.addRow("Base URL", self.base_url_input)
        form.addRow("Model", self.model_input)
        form.addRow("超时时间", self.timeout_spin)
        form.addRow("", self.enabled_check)

        layout.addLayout(form)

        self.test_button = QPushButton("测试连接", self)
        self.test_button.clicked.connect(self._test_connection)
        self.test_status = QLabel("", self)
        self.test_status.setWordWrap(True)
        test_row = QHBoxLayout()
        test_row.addWidget(self.test_button)
        test_row.addWidget(self.test_status, 1)
        layout.addLayout(test_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_settings(self) -> None:
        settings = load_ai_settings(self.data_root)
        self.api_key_input.setText(settings.api_key)
        self.base_url_input.setText(settings.base_url)
        self.model_input.setText(settings.model)
        self.timeout_spin.setValue(settings.timeout_seconds)
        self.enabled_check.setChecked(settings.enabled)

    def _save_and_accept(self) -> None:
        settings = AISettings(
            api_key=self.api_key_input.text().strip(),
            base_url=self.base_url_input.text().strip() or DEFAULT_BASE_URL,
            model=self.model_input.text().strip() or DEFAULT_MODEL,
            enabled=self.enabled_check.isChecked(),
            timeout_seconds=self.timeout_spin.value(),
        )
        save_ai_settings(self.data_root, settings)
        logger.info("AI 设置已保存: enabled=%s model=%s", settings.enabled, settings.model)
        self.accept()

    def _test_connection(self) -> None:
        settings = AISettings(
            api_key=self.api_key_input.text().strip(),
            base_url=self.base_url_input.text().strip() or DEFAULT_BASE_URL,
            model=self.model_input.text().strip() or DEFAULT_MODEL,
            enabled=True,
            timeout_seconds=self.timeout_spin.value(),
        )
        temp_root = self.data_root
        save_ai_settings(temp_root, settings)
        self.test_status.setText("正在测试连接...")
        self.test_status.setStyleSheet("color: #666;")
        self.test_button.setEnabled(False)
        try:
            result = test_ai_connection(temp_root)
            self.test_status.setText(f"连接成功！模型返回: {result}")
            self.test_status.setStyleSheet("color: #2e7d32; font-weight: 600;")
        except Exception as exc:
            self.test_status.setText(f"连接失败: {exc}")
            self.test_status.setStyleSheet("color: #c62828;")
        finally:
            self.test_button.setEnabled(True)


class AIPreviewDialog(QDialog):
    """Show AI-generated content preview before applying."""

    def __init__(
        self,
        title: str,
        preview_text: str,
        warning: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(640, 480)
        self._confirmed = False
        self._build_ui(preview_text, warning)

    def _build_ui(self, preview_text: str, warning: str) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if warning:
            warn_label = QLabel(warning, self)
            warn_label.setStyleSheet(
                "background: #fff3e0; color: #e65100; padding: 8px; "
                "border: 1px solid #ffb74d; border-radius: 6px; font-weight: 600;"
            )
            warn_label.setWordWrap(True)
            layout.addWidget(warn_label)

        title_label = QLabel("AI 生成的内容预览", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(title_label)

        self.preview_edit = QTextEdit(self)
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlainText(preview_text)
        layout.addWidget(self.preview_edit, 1)

        buttons = QDialogButtonBox(self)
        self.apply_button = QPushButton("应用", self)
        self.apply_button.setStyleSheet(
            "QPushButton { background: #2e7d32; color: #fff; font-weight: 600; "
            "padding: 8px 20px; border-radius: 6px; }"
            "QPushButton:hover { background: #388e3c; }"
        )
        cancel_button = QPushButton("取消", self)
        buttons.addButton(self.apply_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._on_apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_apply(self) -> None:
        self._confirmed = True
        self.accept()

    @property
    def is_confirmed(self) -> bool:
        return self._confirmed
