from __future__ import annotations

import math
import time
from typing import Any

from app.core.config import settings
from app.schemas.telemetry import LiveTelemetrySnapshot
from app.services.native_bridge import NativeBridgeProvider
from app.services.track_store import TrackStore
from app.services.windows_shared_memory import WindowsSharedMemoryProvider


class LiveTelemetryService:
    def __init__(self) -> None:
        self.track_store = TrackStore()
        self.native_bridge = NativeBridgeProvider()
        self.shared_memory = WindowsSharedMemoryProvider()

    def get_snapshot(self, track_id: str = "imola") -> LiveTelemetrySnapshot:
        track = self.track_store.get_track(track_id)
        live_state = self._get_real_state()
        if live_state:
            return self._build_real_snapshot(track_id=track_id, track=track, state=live_state)
        return self._build_demo_snapshot(track_id=track_id, track=track)

    def _get_real_state(self) -> dict[str, Any] | None:
        mode = (settings.live_mode or "auto").strip().lower()
        providers = []
        if mode == "native_bridge":
            providers = [self.native_bridge.poll]
        elif mode == "shared_memory":
            providers = [self.shared_memory.poll]
        elif mode == "demo":
            providers = []
        else:
            providers = [self.native_bridge.poll, self.shared_memory.poll]

        for provider in providers:
            state = provider()
            if state:
                return state
        return None

    def _build_real_snapshot(self, track_id: str, track: dict[str, Any], state: dict[str, Any]) -> LiveTelemetrySnapshot:
        reference = track.get("reference_line", {})
        polyline = reference.get("polyline") or []
        progress = max(0.0, min(0.9999, float(state.get("progress", 0.0))))
        x, y = self._point_on_polyline(polyline, progress)
        corners = track.get("corners", [])
        current_corner_id = self._corner_for_progress(corners, progress)
        best_lap_s = self._safe_float(state.get("best_lap_s"))
        last_lap_s = self._safe_float(state.get("last_lap_s"))
        lap_delta_s = 0.0
        if best_lap_s and last_lap_s:
            lap_delta_s = round(last_lap_s - best_lap_s, 3)

        return LiveTelemetrySnapshot(
            mode=str(state.get("mode", "shared_memory")),
            source=str(state.get("source", "shared_memory")),
            status=state.get("status"),
            track_id=track_id,
            track_name=state.get("track_name") or track.get("track", {}).get("display_name"),
            progress=round(progress, 4),
            x=round(x, 4),
            y=round(y, 4),
            speed_kph=round(float(state.get("speed_kph", 0.0)), 1),
            throttle_pct=round(float(state.get("throttle_pct", 0.0)), 1),
            brake_pct=round(float(state.get("brake_pct", 0.0)), 1),
            steering_deg=round(float(state.get("steering_deg", 0.0)), 1),
            gear=int(state.get("gear", 1)),
            current_lap=max(1, int(state.get("current_lap", 1))),
            lap_delta_s=lap_delta_s,
            best_lap_s=best_lap_s,
            last_lap_s=last_lap_s,
            current_corner_id=current_corner_id,
            timestamp_ms=int(time.time() * 1000),
        )

    def _build_demo_snapshot(self, track_id: str, track: dict[str, Any]) -> LiveTelemetrySnapshot:
        reference = track.get("reference_line", {})
        polyline = reference.get("polyline") or []
        if len(polyline) < 2:
            polyline = [{"x": 0.12, "y": 0.65}, {"x": 0.88, "y": 0.65}]

        corners = track.get("corners", [])
        cycle_s = 104.6
        now = time.time()
        progress = (now % cycle_s) / cycle_s
        x, y = self._point_on_polyline(polyline, progress)
        current_corner_id = self._corner_for_progress(corners, progress)

        brake_markers = reference.get("brake_markers", [])
        nearest_brake = min((abs(progress - float(marker.get("progress", 0.0))) for marker in brake_markers), default=1.0)
        braking_factor = max(0.0, 1.0 - nearest_brake * 9.0)
        base_speed = 235.0 - braking_factor * 150.0 + 18.0 * math.sin(now * 0.55)
        speed_kph = max(68.0, min(302.0, base_speed))
        brake_pct = round(max(0.0, min(100.0, braking_factor * 115.0)), 1)
        throttle_pct = round(max(0.0, min(100.0, 100.0 - brake_pct - abs(math.sin(now * 0.7)) * 10.0)), 1)
        steering_deg = round(math.sin(now * 1.85) * (9 + braking_factor * 18), 1)
        lap_delta_s = round(math.sin(now * 0.23) * 0.28 + (0.12 if braking_factor > 0.35 else 0.0), 3)
        gear = max(1, min(7, int(round((speed_kph - 50) / 35.0))))
        current_lap = int(now // cycle_s) % 999 + 1
        fallback_notes = []
        if settings.live_mode != "demo":
            if self.native_bridge.load_error:
                fallback_notes.append(f"native bridge: {self.native_bridge.load_error}")
            if self.shared_memory.last_error:
                fallback_notes.append(f"shared memory: {self.shared_memory.last_error}")
        status = "; ".join(fallback_notes) if fallback_notes else "Demo/live fallback feed active"

        return LiveTelemetrySnapshot(
            mode="demo",
            source="demo_fallback",
            status=status,
            track_id=track_id,
            track_name=track.get("track", {}).get("display_name"),
            progress=round(progress, 4),
            x=round(x, 4),
            y=round(y, 4),
            speed_kph=round(speed_kph, 1),
            throttle_pct=throttle_pct,
            brake_pct=brake_pct,
            steering_deg=steering_deg,
            gear=gear,
            current_lap=current_lap,
            lap_delta_s=lap_delta_s,
            best_lap_s=None,
            last_lap_s=None,
            current_corner_id=current_corner_id,
            timestamp_ms=int(now * 1000),
        )

    def _corner_for_progress(self, corners: list[dict[str, Any]], progress: float) -> str | None:
        if not corners:
            return None
        best_corner = None
        best_distance = 999.0
        for corner in corners:
            corner_progress = float(corner.get("progress", 0.0))
            distance = min(abs(progress - corner_progress), 1.0 - abs(progress - corner_progress))
            if distance < best_distance:
                best_distance = distance
                best_corner = corner
        return best_corner.get("id") if best_corner else None

    def _point_on_polyline(self, polyline: list[dict[str, float]], progress: float) -> tuple[float, float]:
        points = [(float(point["x"]), float(point["y"])) for point in polyline]
        if len(points) == 1:
            return points[0]

        lengths: list[float] = []
        total = 0.0
        for idx in range(len(points)):
            x1, y1 = points[idx]
            x2, y2 = points[(idx + 1) % len(points)]
            segment = math.dist((x1, y1), (x2, y2))
            lengths.append(segment)
            total += segment

        target = total * progress
        traversed = 0.0
        for idx, segment in enumerate(lengths):
            if traversed + segment >= target:
                start = points[idx]
                end = points[(idx + 1) % len(points)]
                local = 0.0 if segment == 0 else (target - traversed) / segment
                x = start[0] + (end[0] - start[0]) * local
                y = start[1] + (end[1] - start[1]) * local
                return x, y
            traversed += segment
        return points[-1]

    def _safe_float(self, value: Any) -> float | None:
        try:
            if value is None:
                return None
            result = float(value)
            return None if result <= 0 else result
        except (TypeError, ValueError):
            return None
