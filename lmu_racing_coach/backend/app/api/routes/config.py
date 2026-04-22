from fastapi import APIRouter

from app.core.config import settings
from app.services.lmu_locator import LMULocator

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/lmu-path")
def get_lmu_path() -> dict[str, str | None]:
    locator = LMULocator()
    root = locator.detect_lmu_root()
    telemetry = locator.detect_telemetry_dir()
    return {
        "configured_lmu_root": str(settings.lmu_root) if settings.lmu_root else None,
        "detected_lmu_root": str(root) if root else None,
        "detected_telemetry_dir": str(telemetry) if telemetry else None,
    }
