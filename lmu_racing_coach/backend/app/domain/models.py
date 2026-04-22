from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TelemetryFile:
    path: Path
    size_bytes: int
    modified_ts: float
    tables: list[str] = field(default_factory=list)
    schema: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


@dataclass(slots=True)
class CoachingSuggestion:
    corner_id: str | None
    severity: str
    title: str
    detail: str
    expected_gain_s: float
    confidence: float
