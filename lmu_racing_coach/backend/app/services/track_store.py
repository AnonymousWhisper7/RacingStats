from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import settings


class TrackStore:
    def get_track(self, track_id: str) -> dict[str, Any]:
        track_dir = settings.track_data_dir / track_id
        if not track_dir.exists():
            raise FileNotFoundError(track_dir)

        payload: dict[str, Any] = {"track_id": track_id}
        for name in ["track.json", "corners.json", "reference_line.json", "coach_rules.json"]:
            file_path = track_dir / name
            if file_path.exists():
                payload[name.replace(".json", "")] = json.loads(file_path.read_text(encoding="utf-8"))
        return payload
