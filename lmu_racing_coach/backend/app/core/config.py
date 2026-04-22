from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LMU_COACH_", extra="ignore")

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8080)
    steam_root: Optional[Path] = None
    lmu_root: Optional[Path] = None
    telemetry_dir: Optional[Path] = None
    app_data_dir: Path = Field(default=Path.home() / ".lmu_racing_coach")
    track_data_dir: Path = Field(default=Path(__file__).resolve().parents[3] / "data" / "tracks")

    live_mode: str = Field(default="auto")  # auto | native_bridge | shared_memory | demo
    native_bridge_path: Optional[Path] = None
    shared_memory_prefix: str = Field(default="rFactor2SMMP_")
    shared_memory_telemetry_name: Optional[str] = None
    shared_memory_scoring_name: Optional[str] = None
    websocket_live_hz: float = Field(default=10.0)


settings = Settings()
