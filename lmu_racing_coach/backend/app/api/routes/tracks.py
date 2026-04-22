from fastapi import APIRouter, HTTPException

from app.services.track_store import TrackStore

router = APIRouter(prefix="/tracks", tags=["tracks"])

store = TrackStore()


@router.get("/{track_id}")
def get_track(track_id: str) -> dict:
    try:
        return store.get_track(track_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
