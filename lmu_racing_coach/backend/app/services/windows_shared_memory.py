from __future__ import annotations

import ctypes
import math
import sys
from typing import Any

from app.core.config import settings

if sys.platform == "win32":  # pragma: no cover - windows only
    kernel32 = ctypes.windll.kernel32
else:  # pragma: no cover - non-windows fallback
    kernel32 = None

FILE_MAP_READ = 0x0004


class Vec3(ctypes.Structure):
    _pack_ = 4
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class PartialVehicleTelemetry(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mID", ctypes.c_long),
        ("mDeltaTime", ctypes.c_double),
        ("mElapsedTime", ctypes.c_double),
        ("mLapNumber", ctypes.c_long),
        ("mLapStartET", ctypes.c_double),
        ("mVehicleName", ctypes.c_char * 64),
        ("mTrackName", ctypes.c_char * 64),
        ("mPos", Vec3),
        ("mLocalVel", Vec3),
        ("mLocalAccel", Vec3),
        ("mOri", Vec3 * 3),
        ("mLocalRot", Vec3),
        ("mLocalRotAccel", Vec3),
        ("mGear", ctypes.c_long),
        ("mEngineRPM", ctypes.c_double),
        ("mEngineWaterTemp", ctypes.c_double),
        ("mEngineOilTemp", ctypes.c_double),
        ("mClutchRPM", ctypes.c_double),
        ("mUnfilteredThrottle", ctypes.c_double),
        ("mUnfilteredBrake", ctypes.c_double),
        ("mUnfilteredSteering", ctypes.c_double),
        ("mUnfilteredClutch", ctypes.c_double),
        ("mFilteredThrottle", ctypes.c_double),
        ("mFilteredBrake", ctypes.c_double),
        ("mFilteredSteering", ctypes.c_double),
        ("mFilteredClutch", ctypes.c_double),
    ]


class TelemetryMap(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mBytesUpdatedHint", ctypes.c_int),
        ("mNumVehicles", ctypes.c_long),
        ("mVehicles", PartialVehicleTelemetry * 128),
    ]


class PartialScoringInfo(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mTrackName", ctypes.c_char * 64),
        ("mSession", ctypes.c_long),
        ("mCurrentET", ctypes.c_double),
        ("mEndET", ctypes.c_double),
        ("mMaxLaps", ctypes.c_long),
        ("mLapDist", ctypes.c_double),
        ("pointer1", ctypes.c_ubyte * 8),
        ("mNumVehicles", ctypes.c_long),
    ]


class PartialVehicleScoring(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mID", ctypes.c_long),
        ("mDriverName", ctypes.c_char * 32),
        ("mVehicleName", ctypes.c_char * 64),
        ("mTotalLaps", ctypes.c_short),
        ("mSector", ctypes.c_byte),
        ("mFinishStatus", ctypes.c_byte),
        ("mLapDist", ctypes.c_double),
        ("mPathLateral", ctypes.c_double),
        ("mTrackEdge", ctypes.c_double),
        ("mBestSector1", ctypes.c_double),
        ("mBestSector2", ctypes.c_double),
        ("mBestLapTime", ctypes.c_double),
        ("mLastSector1", ctypes.c_double),
        ("mLastSector2", ctypes.c_double),
        ("mLastLapTime", ctypes.c_double),
        ("mCurSector1", ctypes.c_double),
        ("mCurSector2", ctypes.c_double),
        ("mNumPitstops", ctypes.c_short),
        ("mNumPenalties", ctypes.c_short),
        ("mIsPlayer", ctypes.c_bool),
        ("mControl", ctypes.c_byte),
        ("mInPits", ctypes.c_bool),
        ("mPlace", ctypes.c_ubyte),
        ("mVehicleClass", ctypes.c_char * 32),
        ("mTimeBehindNext", ctypes.c_double),
        ("mLapsBehindNext", ctypes.c_long),
        ("mTimeBehindLeader", ctypes.c_double),
        ("mLapsBehindLeader", ctypes.c_long),
        ("mLapStartET", ctypes.c_double),
        ("mPos", Vec3),
        ("mLocalVel", Vec3),
    ]


class ScoringMap(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mBytesUpdatedHint", ctypes.c_int),
        ("mScoringInfo", PartialScoringInfo),
        ("mVehicles", PartialVehicleScoring * 128),
    ]


class WindowsSharedMemoryProvider:
    def __init__(self) -> None:
        prefix = settings.shared_memory_prefix or "rFactor2SMMP_"
        self.telemetry_name = settings.shared_memory_telemetry_name or f"{prefix}Telemetry"
        self.scoring_name = settings.shared_memory_scoring_name or f"{prefix}Scoring"
        self.last_error: str | None = None

    def poll(self) -> dict[str, Any] | None:
        if sys.platform != "win32":
            self.last_error = "Windows shared memory is only available on Windows"
            return None

        telemetry = self._read_struct(self.telemetry_name, TelemetryMap)
        scoring = self._read_struct(self.scoring_name, ScoringMap)
        if telemetry is None or scoring is None:
            return None

        if telemetry.mNumVehicles <= 0 or scoring.mScoringInfo.mNumVehicles <= 0:
            self.last_error = "Shared memory opened but no vehicles were exposed"
            return None

        player_scoring = None
        scoring_count = max(0, min(int(scoring.mScoringInfo.mNumVehicles), 128))
        for idx in range(scoring_count):
            vehicle = scoring.mVehicles[idx]
            if bool(vehicle.mIsPlayer):
                player_scoring = vehicle
                break
        if player_scoring is None:
            self.last_error = "Player vehicle not found in scoring buffer"
            return None

        telemetry_count = max(0, min(int(telemetry.mNumVehicles), 128))
        player_telemetry = None
        for idx in range(telemetry_count):
            vehicle = telemetry.mVehicles[idx]
            if int(vehicle.mID) == int(player_scoring.mID):
                player_telemetry = vehicle
                break
        if player_telemetry is None:
            # fall back to first telemetry sample if IDs did not match yet
            player_telemetry = telemetry.mVehicles[0]

        speed_ms = math.sqrt(
            float(player_telemetry.mLocalVel.x) ** 2
            + float(player_telemetry.mLocalVel.y) ** 2
            + float(player_telemetry.mLocalVel.z) ** 2
        )
        track_length_m = float(scoring.mScoringInfo.mLapDist) if float(scoring.mScoringInfo.mLapDist) > 0 else 0.0
        lap_dist_m = max(0.0, float(player_scoring.mLapDist))
        progress = (lap_dist_m / track_length_m) if track_length_m > 0 else 0.0
        progress = max(0.0, min(0.9999, progress))

        track_name = self._decode(scoring.mScoringInfo.mTrackName) or self._decode(player_telemetry.mTrackName)
        return {
            "mode": "shared_memory",
            "source": self.telemetry_name,
            "track_name": track_name,
            "progress": progress,
            "speed_kph": speed_ms * 3.6,
            "throttle_pct": max(0.0, min(100.0, float(player_telemetry.mFilteredThrottle) * 100.0)),
            "brake_pct": max(0.0, min(100.0, float(player_telemetry.mFilteredBrake) * 100.0)),
            "steering_deg": max(-540.0, min(540.0, float(player_telemetry.mFilteredSteering) * 450.0)),
            "gear": int(player_telemetry.mGear),
            "current_lap": max(1, int(player_telemetry.mLapNumber)),
            "best_lap_s": None if float(player_scoring.mBestLapTime) <= 0 else float(player_scoring.mBestLapTime),
            "last_lap_s": None if float(player_scoring.mLastLapTime) <= 0 else float(player_scoring.mLastLapTime),
            "status": f"Using shared memory maps {self.telemetry_name} and {self.scoring_name}",
        }

    def _read_struct(self, mapping_name: str, struct_type: type[ctypes.Structure]):
        size = ctypes.sizeof(struct_type)
        raw = self._read_mapping(mapping_name, size)
        if raw is None:
            return None
        return struct_type.from_buffer_copy(raw)

    def _read_mapping(self, mapping_name: str, size: int) -> bytes | None:
        if kernel32 is None:  # pragma: no cover - non-windows
            return None
        handle = kernel32.OpenFileMappingW(FILE_MAP_READ, False, mapping_name)
        if not handle:
            self.last_error = f"Could not open shared memory map: {mapping_name}"
            return None
        kernel32.MapViewOfFile.restype = ctypes.c_void_p
        ptr = kernel32.MapViewOfFile(handle, FILE_MAP_READ, 0, 0, size)
        if not ptr:
            kernel32.CloseHandle(handle)
            self.last_error = f"Could not map shared memory view: {mapping_name}"
            return None
        try:
            return ctypes.string_at(ptr, size)
        finally:
            kernel32.UnmapViewOfFile(ctypes.c_void_p(ptr))
            kernel32.CloseHandle(handle)

    def _decode(self, raw: bytes) -> str | None:
        return raw.split(b"\x00", 1)[0].decode("utf-8", errors="ignore") or None
