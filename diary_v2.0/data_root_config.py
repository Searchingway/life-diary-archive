from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Callable


class DataRootError(ValueError):
    pass


def default_bootstrap_path() -> Path:
    local_app_data = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    return local_app_data / "LifeDiary" / "bootstrap.json"


def _read_bootstrap(path: Path) -> dict[str, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    root = value.get("data_root")
    return {"data_root": root} if isinstance(root, str) and root.strip() else {}


def resolve_data_root(default_root: Path, bootstrap_path: Path | None = None) -> Path:
    configured = os.environ.get("LIFE_DIARY_DATA_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    bootstrap = _read_bootstrap(bootstrap_path or default_bootstrap_path())
    if bootstrap.get("data_root"):
        return Path(bootstrap["data_root"]).expanduser().resolve()
    return default_root.resolve()


def write_bootstrap(data_root: Path, bootstrap_path: Path | None = None) -> None:
    path = bootstrap_path or default_bootstrap_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"data_root": str(data_root.resolve())}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def migrate_data_root(
    source_root: Path,
    destination_root: Path,
    bootstrap_path: Path | None = None,
    copier: Callable[[str, str], str] = shutil.copytree,
) -> Path:
    source = source_root.expanduser().resolve()
    destination = destination_root.expanduser().resolve()
    if not source.exists() or not source.is_dir() or not any(source.iterdir()):
        raise DataRootError("当前数据目录不存在或为空，无法迁移")
    if source == destination:
        raise DataRootError("新目录不能与当前数据目录相同")
    if destination.exists():
        raise DataRootError("新目录已存在；为避免覆盖数据，本次迁移未执行")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        copier(str(source), str(destination))
        copied = {child.name for child in destination.iterdir()}
        required = {child.name for child in source.iterdir()}
        if copied != required:
            raise DataRootError("复制后的目录校验失败")
        write_bootstrap(destination, bootstrap_path)
        return destination
    except Exception as exc:
        if destination.exists():
            shutil.rmtree(destination)
        if isinstance(exc, DataRootError):
            raise
        raise DataRootError(f"迁移失败：{exc}") from exc
