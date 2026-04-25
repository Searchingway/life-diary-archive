from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path


MODULE_DIRECTORIES = {
    "diary": ("entries", "日记"),
    "footprint": ("footprints", "足迹"),
    "book": ("books", "读书"),
}


class ExchangePackageExporter:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)

    def export_module(self, module: str, target_dir: Path | str) -> Path:
        if module not in MODULE_DIRECTORIES:
            raise ValueError(f"未知导出模块：{module}")

        folder_name, title = MODULE_DIRECTORIES[module]
        source_dir = self.root_dir / folder_name
        if not source_dir.exists():
            raise FileNotFoundError(f"暂无可导出的{title}数据。")

        files = [path for path in source_dir.rglob("*") if path.is_file()]
        if not files:
            raise FileNotFoundError(f"暂无可导出的{title}数据。")

        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self._unique_path(target / f"life_diary_{module}_{timestamp}.zip")
        manifest = {
            "app": "life_diary",
            "package_version": 1,
            "module": module,
            "module_title": title,
            "data_directory": folder_name,
            "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "file_count": len(files),
        }

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for file_path in files:
                archive.write(file_path, f"{folder_name}/{file_path.relative_to(source_dir).as_posix()}")

        return zip_path

    def _unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        counter = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
            if not candidate.exists():
                return candidate
            counter += 1
