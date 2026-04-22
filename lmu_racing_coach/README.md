# LMU Racing Coach

Local-first racing coach for **Le Mans Ultimate** with:
- Steam-linked user identity
- LMU telemetry ingestion
- lap analysis and coaching suggestions
- track-aware metadata packs
- optional future live overlay/shared-memory bridge

## Repository layout

- `backend/` Python FastAPI analytics and local API
- `frontend/` React + TypeScript desktop UI starter
- `native/` C bridge placeholder for future LMU shared-memory adapter
- `data/` track packs and local data assets
- `docs/` architecture and implementation notes

## Current scope

This starter focuses on the **stable telemetry path**:
1. LMU records telemetry locally to DuckDB
2. Python ingests and inspects telemetry files
3. Python normalizes laps/corners where possible
4. a coaching engine emits post-lap suggestions
5. a frontend can render track and coaching cards

## Quick start (backend)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload --port 8080
```

Then open:
- `GET http://127.0.0.1:8080/health`
- `GET http://127.0.0.1:8080/config/lmu-path`
- `POST http://127.0.0.1:8080/telemetry/scan`

## Planned next steps

- wire in real LMU DuckDB schema from a sample session
- render Imola track map in the frontend
- add corner-phase delta analysis
- add voice/overlay coaching mode
- replace the native C bridge placeholder with a real shared-memory adapter


## Dashboard v2

This package adds:
- live track map panel
- live telemetry bars
- coaching cards
- lap summary widgets
- sector widgets
- `/telemetry/live` demo endpoint for a moving car dot fallback


## Live adapter upgrade

- Added WebSocket live feed at `/telemetry/live/ws`
- Added Windows shared-memory compatibility provider
- Added native bridge loader and build stub
- Added docs for auto / shared_memory / native_bridge / demo modes
