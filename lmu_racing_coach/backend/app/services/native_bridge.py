from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

from app.core.config import settings


class NativeBridgeUnavailable(RuntimeError):
    pass


class LMUBridgeSample(ctypes.Structure):
    _fields_ = [
        ("session_time_s", ctypes.c_double),
        ("lap_distance_fraction", ctypes.c_double),
        ("speed_kph", ctypes.c_double),
        ("throttle", ctypes.c_double),
        ("brake", ctypes.c_double),
        ("steer", ctypes.c_double),
        ("gear", ctypes.c_int),
        ("lap_number", ctypes.c_int),
        ("best_lap_s", ctypes.c_double),
        ("last_lap_s", ctypes.c_double),
    ]


class NativeBridgeProvider:
    def __init__(self) -> None:
        self._dll = None
        self._load_error: str | None = None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def poll(self) -> dict[str, Any] | None:
        dll = self._load_dll()
        if dll is None:
            return None
        sample = LMUBridgeSample()
        result = dll.lmu_bridge_poll(ctypes.byref(sample))
        if result != 0:
            return None
        return {
            "mode": "native_bridge",
            "source": "native_bridge_dll",
            "progress": max(0.0, min(0.9999, float(sample.lap_distance_fraction))),
            "speed_kph": float(sample.speed_kph),
            "throttle_pct": max(0.0, min(100.0, float(sample.throttle) * 100.0)),
            "brake_pct": max(0.0, min(100.0, float(sample.brake) * 100.0)),
            "steering_deg": float(sample.steer),
            "gear": int(sample.gear),
            "current_lap": int(sample.lap_number),
            "best_lap_s": None if sample.best_lap_s <= 0 else float(sample.best_lap_s),
            "last_lap_s": None if sample.last_lap_s <= 0 else float(sample.last_lap_s),
        }

    def _load_dll(self):
        if self._dll is not None:
            return self._dll
        dll_path = self._resolve_dll_path()
        if dll_path is None:
            self._load_error = "Native bridge DLL not found"
            return None
        try:
            dll = ctypes.WinDLL(str(dll_path))
            dll.lmu_bridge_initialize.restype = ctypes.c_int
            dll.lmu_bridge_poll.argtypes = [ctypes.POINTER(LMUBridgeSample)]
            dll.lmu_bridge_poll.restype = ctypes.c_int
            dll.lmu_bridge_shutdown.restype = None
            init_result = dll.lmu_bridge_initialize()
            if init_result != 0:
                self._load_error = f"Native bridge initialization failed with code {init_result}"
                return None
            self._dll = dll
            return self._dll
        except Exception as exc:  # pragma: no cover - depends on user system
            self._load_error = str(exc)
            return None

    def _resolve_dll_path(self) -> Path | None:
        if settings.native_bridge_path and settings.native_bridge_path.exists():
            return settings.native_bridge_path
        candidates = [
            Path(__file__).resolve().parents[3] / "native" / "lmu_bridge" / "build" / "lmu_bridge.dll",
            Path(__file__).resolve().parents[3] / "native" / "lmu_bridge" / "build" / "Release" / "lmu_bridge.dll",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None
