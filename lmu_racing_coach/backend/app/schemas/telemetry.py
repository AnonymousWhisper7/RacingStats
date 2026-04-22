from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryFileSummary(BaseModel):
    path: str
    size_bytes: int
    modified_ts: float
    tables: list[str] = Field(default_factory=list)


class TelemetryFileDetail(TelemetryFileSummary):
    schema: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class ScanTelemetryResponse(BaseModel):
    root: str
    files: list[TelemetryFileSummary]


class AnalyzeTelemetryRequest(BaseModel):
    file_path: str | None = None


class AnalyzedLap(BaseModel):
    lap_index: int
    lap_time_s: float | None = None
    max_speed_kph: float | None = None
    avg_speed_kph: float | None = None
    notes: list[str] = Field(default_factory=list)


class CoachingSuggestionModel(BaseModel):
    corner_id: str | None = None
    severity: str
    title: str
    detail: str
    expected_gain_s: float
    confidence: float


class AnalyzeTelemetryResponse(BaseModel):
    source_file: str
    tables: list[str]
    inferred_channels: dict[str, str | None]
    laps: list[AnalyzedLap]
    suggestions: list[CoachingSuggestionModel]
    debug: dict[str, Any] = Field(default_factory=dict)


class LiveTelemetrySnapshot(BaseModel):
    mode: str = "demo"
    source: str = "demo_fallback"
    status: str | None = None
    track_id: str = "imola"
    track_name: str | None = None
    progress: float = 0.0
    x: float = 0.0
    y: float = 0.0
    speed_kph: float = 0.0
    throttle_pct: float = 0.0
    brake_pct: float = 0.0
    steering_deg: float = 0.0
    gear: int = 1
    current_lap: int = 1
    lap_delta_s: float = 0.0
    best_lap_s: float | None = None
    last_lap_s: float | None = None
    current_corner_id: str | None = None
    timestamp_ms: int
