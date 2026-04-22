# LMU Racing Coach Architecture

## 1. Language split and file extensions

### Desktop shell and UI
- **TypeScript / React**: `.ts`, `.tsx`
- **HTML shell**: `.html`
- **CSS**: `.css`
- **Optional Tauri desktop shell**: Rust `.rs`, config `.toml`

### Analytics and local API
- **Python**: `.py`
- FastAPI endpoints
- telemetry ingestion
- lap analysis
- coaching engine
- track pack loading

### Native low-latency bridge (future)
- **C**: `.c`, `.h`
- or **C++**: `.cpp`, `.hpp`
- used only when we implement a real shared-memory/plugin adapter for near-real-time coaching

### Data and configuration
- **JSON**: `.json`
- **YAML**: `.yml` / `.yaml` if needed later
- **DuckDB database files**: `.duckdb`
- **SVG assets**: `.svg`
- **Parquet exports**: `.parquet` for analytics cache if needed

## 2. Runtime architecture

```text
LMU Game
  ├─ Native telemetry recording -> DuckDB files
  └─ Optional plugin/shared memory -> native C bridge (future)

Local Coach Runtime
  ├─ Python FastAPI backend
  │   ├─ LMU locator
  │   ├─ telemetry ingestor
  │   ├─ lap analyzer
  │   ├─ coaching engine
  │   └─ track store
  └─ React/TypeScript UI
      ├─ session dashboard
      ├─ track visualization
      ├─ lap table
      └─ coaching cards
```

## 3. Why this split

- Python is the fastest way to build telemetry analytics and coaching logic.
- TypeScript/React is the fastest way to build a rich desktop UI.
- C/C++ should be introduced only for the part that really benefits from it: low-latency shared-memory reading or performance-critical geometric processing.
- This keeps version 1 stable because it depends first on LMU's native telemetry files.

## 4. Initial coding order

1. LMU path and telemetry discovery
2. DuckDB schema inspection
3. telemetry normalization
4. lap summary extraction
5. coaching heuristics
6. track metadata and Imola corner map
7. UI integration
8. shared-memory bridge

## 5. Planned future modules

- `backend/app/services/normalizer.py`
- `backend/app/services/corner_phase_detector.py`
- `backend/app/services/reference_lap_builder.py`
- `backend/app/services/delta_by_distance.py`
- `frontend/src/components/TrackMap.tsx`
- `frontend/src/components/CornerCard.tsx`
- `native/lmu_bridge/src/windows_shared_memory_reader.c`
