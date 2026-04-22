from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TrackStore:
    def __init__(self) -> None:
        self.base_path = Path(__file__).resolve().parents[3] / "data" / "tracks"

    def get_track(self, track_id: str) -> dict[str, Any]:
        track_path = self.base_path / track_id
        if not track_path.exists():
            raise FileNotFoundError(f"Track pack not found: {track_id}")

        return {
            "track_id": track_id,
            "track": self._read_json(track_path / "track.json"),
            "corners": self._read_json(track_path / "corners.json"),
            "reference_line": self._read_json(track_path / "reference_line.json"),
            "coach_rules": self._read_json(track_path / "coach_rules.json"),
            "map_svg": self._read_json_optional(track_path / "map_svg.json"),
        }

    def _read_json(self, path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Missing track file: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_json_optional(self, path: Path) -> Any:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
