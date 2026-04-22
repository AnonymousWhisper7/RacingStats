from __future__ import annotations

import os
from pathlib import Path

from app.core.config import settings


class LMULocator:
    def detect_lmu_root(self) -> Path | None:
        if settings.lmu_root and settings.lmu_root.exists():
            return settings.lmu_root

        candidates = []
        if settings.steam_root:
            candidates.append(settings.steam_root / "steamapps" / "common" / "Le Mans Ultimate")

        program_files_x86 = os.environ.get("ProgramFiles(x86)")
        if program_files_x86:
            candidates.append(Path(program_files_x86) / "Steam" / "steamapps" / "common" / "Le Mans Ultimate")

        program_files = os.environ.get("ProgramFiles")
        if program_files:
            candidates.append(Path(program_files) / "Steam" / "steamapps" / "common" / "Le Mans Ultimate")

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def detect_telemetry_dir(self) -> Path | None:
        if settings.telemetry_dir and settings.telemetry_dir.exists():
            return settings.telemetry_dir

        root = self.detect_lmu_root()
        if not root:
            return None

        telemetry = root / "UserData" / "Telemetry"
        return telemetry if telemetry.exists() else None
