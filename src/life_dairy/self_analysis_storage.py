from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import SelfAnalysisEntry, SelfAnalysisImage, SelfAnalysisImageDraft, now_iso


SELF_ANALYSIS_TYPES = [
    "情绪",
    "梦",
    "关系",
    "欲望",
    "重复模式",
    "身体感受",
    "接单焦虑",
    "学习困境",
    "其他",
]

SELF_ANALYSIS_SECTIONS = [
    "触发事件",
    "当时的情绪",
    "当时的身体反应",
    "我表面上想要什么",
    "我真正害怕什么",
    "我真正想要什么",
    "我在重复什么模式",
    "我想象中的别人怎么看我",
    "我采取了什么防御方式",
    "这件事和过去哪些经历相似",
    "我从中看见了什么",
    "下一步我可以怎么做",
]


class SelfAnalysisStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.analyses_dir = self.root_dir / "self_analysis"
        self.analyses_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_analysis(self) -> SelfAnalysisEntry:
        timestamp = now_iso()
        return SelfAnalysisEntry(
            id=uuid4().hex,
            title="",
            date=date.today().isoformat(),
            analysis_type="其他",
            tags=[],
            trigger_event="",
            emotion="",
            body_reaction="",
            surface_want="",
            real_fear="",
            real_want="",
            repeated_pattern="",
            imagined_judgment="",
            defense="",
            similar_experience="",
            insight="",
            next_action="",
            created_at=timestamp,
            updated_at=timestamp,
            images=[],
            related_diaries=[],
            related_lessons=[],
        )

    def analysis_dir(self, analysis_id: str) -> Path:
        return self.analyses_dir / analysis_id

    def image_dir(self, analysis_id: str) -> Path:
        return self.analysis_dir(analysis_id) / "images"

    def resolve_image_path(self, analysis_id: str, image_name: str) -> Path:
        return self.image_dir(analysis_id) / image_name

    def list_analyses(self, query: str = "", analysis_type: str = "全部") -> list[SelfAnalysisEntry]:
        keyword = query.strip().lower()
        selected_type = analysis_type.strip()
        items: list[SelfAnalysisEntry] = []

        for child in self.analyses_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                analysis = self._load_analysis_from_directory(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if selected_type and selected_type != "全部" and analysis.analysis_type != selected_type:
                continue
            if keyword and not self._matches_query(analysis, keyword):
                continue
            items.append(analysis)

        items.sort(key=lambda item: (item.date, item.updated_at, item.created_at), reverse=True)
        return items

    def save_analysis(
        self,
        analysis: SelfAnalysisEntry,
        image_items: Iterable[SelfAnalysisImageDraft] | None = None,
    ) -> SelfAnalysisEntry:
        analysis_dir = self.analysis_dir(analysis.id)
        analysis_dir.mkdir(parents=True, exist_ok=True)

        analysis.updated_at = now_iso()
        if analysis.analysis_type not in SELF_ANALYSIS_TYPES:
            analysis.analysis_type = "其他"

        if image_items is not None:
            analysis.images = self._sync_images(analysis.id, image_items)

        with (analysis_dir / "analysis.json").open("w", encoding="utf-8") as file:
            json.dump(analysis.to_dict(), file, ensure_ascii=False, indent=2)
        (analysis_dir / "content.md").write_text(self._build_content(analysis), encoding="utf-8")
        return self.load_analysis(analysis.id)

    def load_analysis(self, analysis_id: str) -> SelfAnalysisEntry:
        return self._load_analysis_from_directory(self.analysis_dir(analysis_id), include_deleted=True)

    def delete_analysis(self, analysis_id: str) -> None:
        analysis_dir = self.analysis_dir(analysis_id)
        if not analysis_dir.exists():
            raise FileNotFoundError(f"找不到要删除的自我分析记录：{analysis_id}")
        metadata_path = analysis_dir / "analysis.json"
        with metadata_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = now_iso()
        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _load_analysis_from_directory(self, analysis_dir: Path, include_deleted: bool) -> SelfAnalysisEntry:
        with (analysis_dir / "analysis.json").open("r", encoding="utf-8") as file:
            data = json.load(file)

        if data.get("deleted") and not include_deleted:
            raise ValueError("self analysis deleted")

        content_path = analysis_dir / "content.md"
        content = content_path.read_text(encoding="utf-8") if content_path.exists() else ""
        return SelfAnalysisEntry.from_dict(data, self._parse_content(content))

    def _matches_query(self, analysis: SelfAnalysisEntry, keyword: str) -> bool:
        haystacks = [
            analysis.title,
            analysis.date,
            analysis.analysis_type,
            " ".join(analysis.tags),
            analysis.trigger_event,
            analysis.emotion,
            analysis.body_reaction,
            analysis.surface_want,
            analysis.real_fear,
            analysis.real_want,
            analysis.repeated_pattern,
            analysis.imagined_judgment,
            analysis.defense,
            analysis.similar_experience,
            analysis.insight,
            analysis.next_action,
            " ".join(image.label for image in analysis.images if image.label),
            " ".join(item.display_title for item in analysis.related_diaries),
            " ".join(item.display_title for item in analysis.related_lessons),
        ]
        return any(keyword in text.lower() for text in haystacks if text)

    def _build_content(self, analysis: SelfAnalysisEntry) -> str:
        values = {
            "触发事件": analysis.trigger_event,
            "当时的情绪": analysis.emotion,
            "当时的身体反应": analysis.body_reaction,
            "我表面上想要什么": analysis.surface_want,
            "我真正害怕什么": analysis.real_fear,
            "我真正想要什么": analysis.real_want,
            "我在重复什么模式": analysis.repeated_pattern,
            "我想象中的别人怎么看我": analysis.imagined_judgment,
            "我采取了什么防御方式": analysis.defense,
            "这件事和过去哪些经历相似": analysis.similar_experience,
            "我从中看见了什么": analysis.insight,
            "下一步我可以怎么做": analysis.next_action,
        }
        parts = []
        for title in SELF_ANALYSIS_SECTIONS:
            parts.append(f"# {title}\n\n{values.get(title, '').rstrip()}\n")
        return "\n".join(parts).rstrip() + "\n"

    def _parse_content(self, content: str) -> dict[str, str]:
        sections = {title: "" for title in SELF_ANALYSIS_SECTIONS}
        current_title: str | None = None
        current_lines: list[str] = []

        def flush() -> None:
            if current_title in sections:
                sections[current_title] = "\n".join(current_lines).strip()

        for line in content.splitlines():
            if line.startswith("# "):
                flush()
                title = line[2:].strip()
                current_title = title if title in sections else None
                current_lines = []
                continue
            if current_title is not None:
                current_lines.append(line)
        flush()
        return sections

    def _sync_images(
        self,
        analysis_id: str,
        image_items: Iterable[SelfAnalysisImageDraft],
    ) -> list[SelfAnalysisImage]:
        images_dir = self.image_dir(analysis_id)
        images_dir.mkdir(parents=True, exist_ok=True)

        keep_images: list[SelfAnalysisImage] = []
        keep_lookup: set[str] = set()
        seen_sources: set[str] = set()
        images_root = images_dir.resolve()

        for item in image_items:
            source_path = Path(item.source_path)
            if not source_path.exists():
                raise FileNotFoundError(f"找不到图片文件：{source_path}")

            resolved_source = source_path.resolve()
            source_key = str(resolved_source).lower()
            if source_key in seen_sources:
                continue
            seen_sources.add(source_key)

            if resolved_source.is_relative_to(images_root):
                final_name = resolved_source.name
            else:
                final_name = self._copy_image(images_dir, resolved_source)

            if final_name not in keep_lookup:
                keep_images.append(SelfAnalysisImage(file_name=final_name, label=item.label.strip()))
                keep_lookup.add(final_name)

        self._prune_unused_images(images_dir, keep_lookup)
        return keep_images

    def _copy_image(self, images_dir: Path, source_path: Path) -> str:
        target_name = self._unique_name(images_dir, source_path.name)
        shutil.copy2(source_path, images_dir / target_name)
        return target_name

    def _unique_name(self, parent_dir: Path, original_name: str) -> str:
        candidate = Path(original_name).name
        stem = Path(candidate).stem or "image"
        suffix = Path(candidate).suffix
        counter = 1

        while (parent_dir / candidate).exists():
            candidate = f"{stem}_{counter}{suffix}"
            counter += 1
        return candidate

    def _prune_unused_images(self, images_dir: Path, keep_names: set[str]) -> None:
        if not images_dir.exists():
            return

        for child in images_dir.iterdir():
            if child.is_file() and child.name not in keep_names:
                try:
                    child.unlink()
                except OSError:
                    continue
