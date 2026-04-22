from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.schemas.telemetry import (
    AnalyzeTelemetryRequest,
    AnalyzeTelemetryResponse,
    CoachingSuggestionModel,
    LiveTelemetrySnapshot,
    ScanTelemetryResponse,
    TelemetryFileSummary,
)
from app.services.coaching_engine import CoachingEngine
from app.services.lap_analyzer import LapAnalyzer
from app.services.live_telemetry import LiveTelemetryService
from app.services.telemetry_ingestor import TelemetryIngestor

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

ingestor = TelemetryIngestor()
lap_analyzer = LapAnalyzer()
coaching_engine = CoachingEngine()
live_service = LiveTelemetryService()


@router.post("/scan", response_model=ScanTelemetryResponse)
def scan_telemetry() -> ScanTelemetryResponse:
    root, files = ingestor.scan()
    return ScanTelemetryResponse(
        root=str(root) if root else "",
        files=[
            TelemetryFileSummary(
                path=str(file.path),
                size_bytes=file.size_bytes,
                modified_ts=file.modified_ts,
                tables=file.tables,
            )
            for file in files
        ],
    )


@router.post("/inspect")
def inspect_telemetry(payload: AnalyzeTelemetryRequest) -> dict:
    target = _resolve_target_file(payload.file_path)
    try:
        file = ingestor.inspect(target)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "path": str(file.path),
        "size_bytes": file.size_bytes,
        "modified_ts": file.modified_ts,
        "tables": file.tables,
        "schema": file.schema,
    }


@router.post("/analyze", response_model=AnalyzeTelemetryResponse)
def analyze_telemetry(payload: AnalyzeTelemetryRequest) -> AnalyzeTelemetryResponse:
    target = _resolve_target_file(payload.file_path)
    try:
        file = ingestor.inspect(target)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    laps, inferred, debug = lap_analyzer.analyze(target)
    suggestions = coaching_engine.build_suggestions(laps)

    return AnalyzeTelemetryResponse(
        source_file=str(file.path),
        tables=file.tables,
        inferred_channels=inferred,
        laps=laps,
        suggestions=[
            CoachingSuggestionModel(
                corner_id=s.corner_id,
                severity=s.severity,
                title=s.title,
                detail=s.detail,
                expected_gain_s=s.expected_gain_s,
                confidence=s.confidence,
            )
            for s in suggestions
        ],
        debug=debug,
    )


@router.get("/live", response_model=LiveTelemetrySnapshot)
def get_live_snapshot() -> LiveTelemetrySnapshot:
    return live_service.get_snapshot(track_id="imola")


@router.websocket("/live/ws")
async def live_snapshot_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    interval = 1.0 / max(1.0, float(settings.websocket_live_hz))
    try:
        while True:
            snapshot = live_service.get_snapshot(track_id="imola")
            await websocket.send_json(snapshot.model_dump())
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        return


def _resolve_target_file(file_path: str | None) -> Path:
    if file_path:
        return Path(file_path)

    root, files = ingestor.scan()
    if not root or not files:
        raise HTTPException(status_code=404, detail="No LMU telemetry files found")
    return files[0].path
