"""Local AI settings and a non-persisting connection test for Desktop 2.0."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import data_api
from life_dairy.ai_service import AISettings, _build_deepseek_client, load_ai_settings


def _public(settings: AISettings) -> dict[str, Any]:
    values = settings.to_dict()
    values.pop("api_key")
    return {**values, "has_api_key": bool(settings.api_key.strip())}


def read_configuration() -> dict[str, Any]:
    with data_api.data_mutation_lock():
        return _public(load_ai_settings(data_api.DATA_ROOT))


def _draft(payload: dict[str, Any], *, connection_test: bool = False) -> AISettings:
    saved = load_ai_settings(data_api.DATA_ROOT)
    values = saved.to_dict()
    for name in values:
        if name in payload:
            values[name] = payload[name]
    if not isinstance(values["enabled"], bool):
        raise ValueError("启用状态必须是布尔值")
    timeout = values["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 5 <= timeout <= 180:
        raise ValueError("超时时间须为 5 到 180 秒的整数")
    for name in ("api_key", "base_url", "model"):
        if not isinstance(values[name], str):
            raise ValueError("API Key、Base URL 和模型名称必须为文本")
        values[name] = values[name].strip()
    parsed = urlsplit(values["base_url"])
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Base URL 须为有效的 HTTP 或 HTTPS 地址，不包含用户名、密码或查询参数")
    saved_url = urlsplit(saved.base_url)
    if (
        saved.api_key and "api_key" not in payload
        and (parsed.scheme, parsed.hostname, parsed.port) != (saved_url.scheme, saved_url.hostname, saved_url.port)
    ):
        raise ValueError("服务主机已改变，请重新填写该服务的 API Key")
    if not values["model"]:
        raise ValueError("请填写模型名称")
    if (values["enabled"] or connection_test) and not values["api_key"]:
        raise ValueError("请先填写 API Key")
    return AISettings.from_dict(values)


def save_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    with data_api.data_mutation_lock():
        settings = _draft(payload)
        path = data_api.DATA_ROOT / "config" / "ai_settings.json"
        existing = data_api.read_json(path) if path.exists() else {}
        data_api.atomic_write_json(path, {**existing, **settings.to_dict()})
        return _public(settings)


def test_configuration(payload: dict[str, Any]) -> dict[str, Any]:
    # Snapshot the saved key and draft under the lock, then release it before
    # network I/O so a slow provider cannot block diary saves or sync commits.
    with data_api.data_mutation_lock():
        settings = _draft(payload, connection_test=True)
    try:
        client = _build_deepseek_client(settings)
        try:
            response = client.chat.completions.create(
                model=settings.model,
                messages=[{"role": "user", "content": "请仅回复：连接成功"}],
                temperature=0.1,
                max_tokens=50,
                timeout=settings.timeout_seconds,
            )
        finally:
            close = getattr(client, "close", None)
            if close:
                close()
        if not response.choices or not response.choices[0].message.content:
            raise RuntimeError("empty response")
    except Exception as error:
        # Provider exceptions can contain request headers or credentials. Do
        # not log them or return their raw text to the browser.
        status = getattr(error, "status_code", None)
        if status == 401:
            message = "API Key 验证失败，请检查密钥"
        elif status == 429:
            message = "服务限流或额度不足，请稍后重试并检查账户"
        elif "timeout" in type(error).__name__.lower():
            message = "连接测试超时，请检查网络或增加超时时间"
        else:
            message = "连接测试失败，请检查地址、模型、网络及 openai 依赖是否已安装"
        raise RuntimeError(message) from None
    return {"ok": True, "model": settings.model, "message": "连接成功，模型已返回响应；测试未保存设置"}
