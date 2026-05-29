from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .logger import get_logger

logger = get_logger("ai_service")

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 60


@dataclass(slots=True)
class AISettings:
    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    enabled: bool = False
    timeout_seconds: int = DEFAULT_TIMEOUT

    def to_dict(self) -> dict[str, Any]:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "enabled": self.enabled,
            "timeout_seconds": self.timeout_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AISettings":
        return cls(
            api_key=str(data.get("api_key", "")),
            base_url=str(data.get("base_url", DEFAULT_BASE_URL)),
            model=str(data.get("model", DEFAULT_MODEL)),
            enabled=bool(data.get("enabled", False)),
            timeout_seconds=int(data.get("timeout_seconds", DEFAULT_TIMEOUT)),
        )


def _settings_path(data_root: Path) -> Path:
    return data_root / "config" / "ai_settings.json"


def load_ai_settings(data_root: Path) -> AISettings:
    path = _settings_path(data_root)
    if not path.exists():
        return AISettings()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return AISettings.from_dict(data)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        logger.warning("读取 AI 配置失败: %s", exc)
        return AISettings()


def save_ai_settings(data_root: Path, settings: AISettings) -> None:
    path = _settings_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(settings.to_dict(), f, ensure_ascii=False, indent=2)


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


class AIServiceError(Exception):
    pass


class AINotConfiguredError(AIServiceError):
    pass


class AITimeoutError(AIServiceError):
    pass


class AIAPIError(AIServiceError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"API 返回错误 (HTTP {status_code}): {message}")


class AIResponseError(AIServiceError):
    pass


def _build_deepseek_client(settings: AISettings):
    try:
        from openai import OpenAI
    except ImportError:
        raise AIServiceError(
            "未安装 openai 库，请运行: pip install openai"
        )
    return OpenAI(api_key=settings.api_key, base_url=settings.base_url)


def call_ai(
    data_root: Path,
    system_prompt: str,
    user_prompt: str,
    *,
    json_mode: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    settings = load_ai_settings(data_root)
    if not settings.enabled:
        raise AINotConfiguredError("AI 功能未启用，请在 AI 设置中开启并填写 API Key。")
    if not settings.api_key.strip():
        raise AINotConfiguredError("未配置 API Key，请在 AI 设置中填写 DeepSeek API Key。")

    logger.info(
        "调用 AI: model=%s base_url=%s json_mode=%s key=%s",
        settings.model,
        settings.base_url,
        json_mode,
        _mask_key(settings.api_key),
    )

    try:
        client = _build_deepseek_client(settings)
    except AIServiceError:
        raise
    except Exception as exc:
        raise AIServiceError(f"初始化 AI 客户端失败: {exc}")

    kwargs: dict[str, Any] = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": settings.timeout_seconds,
    }

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        error_str = str(exc).lower()
        if "timeout" in error_str or "timed out" in error_str:
            raise AITimeoutError(f"AI 请求超时（{settings.timeout_seconds} 秒），请检查网络或增加超时时间。")
        if hasattr(exc, "status_code"):
            raise AIAPIError(getattr(exc, "status_code", 0), str(exc))
        raise AIServiceError(f"AI 调用失败: {exc}")

    if not response.choices:
        raise AIResponseError("AI 未返回任何内容，请重试。")

    content = response.choices[0].message.content or ""
    logger.info("AI 返回内容长度: %d 字符", len(content))
    return content


def call_ai_json(
    data_root: Path,
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    raw = call_ai(
        data_root,
        system_prompt,
        user_prompt,
        json_mode=True,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AIResponseError(
            f"AI 返回的内容不是合法 JSON，无法解析。\n\n原始返回:\n{raw[:1000]}"
        )
    if not isinstance(result, dict):
        raise AIResponseError(
            f"AI 返回的 JSON 格式不正确（期望对象，实际是 {type(result).__name__}）。\n\n原始返回:\n{raw[:1000]}"
        )
    return result


def test_ai_connection(data_root: Path) -> str:
    """测试 AI 连接，成功返回模型名，失败抛出异常"""
    settings = load_ai_settings(data_root)
    if not settings.api_key.strip():
        raise AINotConfiguredError("未配置 API Key。")
    response = call_ai(
        data_root,
        system_prompt="你是一个助手，请用中文简短回复。",
        user_prompt="请回复: 连接成功",
        temperature=0.1,
        max_tokens=50,
    )
    return response.strip()
