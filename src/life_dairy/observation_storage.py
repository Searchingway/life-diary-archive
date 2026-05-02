from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .models import now_iso


OBSERVATION_EMOTIONS = ["开心", "平静", "焦虑", "难过", "生气", "疲惫", "空虚", "兴奋", "烦躁", "其他"]
OBSERVATION_NEEDS = ["休息", "吃饭", "睡觉", "运动", "找人说话", "继续做事", "暂时放下", "写下来", "其他"]


@dataclass(slots=True)
class ObservationEntry:
    id: str
    time: str
    emotion: str
    intensity: int
    trigger: str
    body_sensation: str
    need: str
    notes: str
    created_at: str
    updated_at: str

    @property
    def display_title(self) -> str:
        suffix = f" 强度{self.intensity}" if self.intensity else ""
        return f"{self.emotion or '未命名观察'}{suffix}"

    @property
    def date(self) -> str:
        return (self.time or self.created_at or "")[:10]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "emotion": self.emotion,
            "intensity": self.intensity,
            "trigger": self.trigger,
            "body_sensation": self.body_sensation,
            "need": self.need,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ObservationEntry":
        try:
            intensity = int(data.get("intensity", 3))
        except (TypeError, ValueError):
            intensity = 3
        return cls(
            id=str(data.get("id", "")),
            time=str(data.get("time", now_iso())),
            emotion=str(data.get("emotion", "平静")),
            intensity=max(1, min(5, intensity)),
            trigger=str(data.get("trigger", "")),
            body_sensation=str(data.get("body_sensation", "")),
            need=str(data.get("need", "写下来")),
            notes=str(data.get("notes", "")),
            created_at=str(data.get("created_at", now_iso())),
            updated_at=str(data.get("updated_at", now_iso())),
        )


class ObservationStorage:
    def __init__(self, root_dir: Path | str):
        self.root_dir = Path(root_dir)
        self.observations_dir = self.root_dir / "observations"
        self.observations_dir.mkdir(parents=True, exist_ok=True)

    def create_empty_observation(self) -> ObservationEntry:
        timestamp = now_iso()
        return ObservationEntry(
            id=uuid4().hex,
            time=timestamp,
            emotion="平静",
            intensity=3,
            trigger="",
            body_sensation="",
            need="写下来",
            notes="",
            created_at=timestamp,
            updated_at=timestamp,
        )

    def observation_dir(self, observation_id: str) -> Path:
        return self.observations_dir / observation_id

    def list_observations(
        self,
        query: str = "",
        emotion: str = "全部",
        intensity: str = "全部",
        date_prefix: str = "",
    ) -> list[ObservationEntry]:
        keyword = query.strip().lower()
        items: list[ObservationEntry] = []
        for child in self.observations_dir.iterdir():
            if not child.is_dir():
                continue
            try:
                observation = self._load_from_dir(child, include_deleted=False)
            except (FileNotFoundError, KeyError, json.JSONDecodeError, OSError, ValueError):
                continue
            if emotion != "全部" and observation.emotion != emotion:
                continue
            if intensity != "全部" and str(observation.intensity) != intensity:
                continue
            if date_prefix and not observation.date.startswith(date_prefix):
                continue
            if keyword and not self._matches_query(observation, keyword):
                continue
            items.append(observation)
        items.sort(key=lambda item: (item.time, item.updated_at), reverse=True)
        return items

    def load_observation(self, observation_id: str) -> ObservationEntry:
        return self._load_from_dir(self.observation_dir(observation_id), include_deleted=True)

    def save_observation(self, observation: ObservationEntry) -> ObservationEntry:
        observation_dir = self.observation_dir(observation.id)
        observation_dir.mkdir(parents=True, exist_ok=True)
        observation.updated_at = now_iso()
        if observation.emotion not in OBSERVATION_EMOTIONS:
            observation.emotion = "其他"
        if observation.need not in OBSERVATION_NEEDS:
            observation.need = "其他"
        observation.intensity = max(1, min(5, int(observation.intensity or 3)))
        (observation_dir / "observation.json").write_text(
            json.dumps(observation.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.load_observation(observation.id)

    def delete_observation(self, observation_id: str) -> None:
        metadata_path = self.observation_dir(observation_id) / "observation.json"
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        data["deleted"] = True
        data["deleted_at"] = now_iso()
        data["updated_at"] = data["deleted_at"]
        metadata_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_dir(self, observation_dir: Path, include_deleted: bool) -> ObservationEntry:
        data = json.loads((observation_dir / "observation.json").read_text(encoding="utf-8"))
        if data.get("deleted") and not include_deleted:
            raise ValueError("observation deleted")
        return ObservationEntry.from_dict(data)

    def _matches_query(self, observation: ObservationEntry, keyword: str) -> bool:
        haystacks = [
            observation.time,
            observation.emotion,
            str(observation.intensity),
            observation.trigger,
            observation.body_sensation,
            observation.need,
            observation.notes,
        ]
        return any(keyword in text.lower() for text in haystacks if text)
