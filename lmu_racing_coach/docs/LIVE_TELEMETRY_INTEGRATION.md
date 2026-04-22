# Live telemetry integration

This package now supports three live modes:

- `auto`: try the native bridge first, then Windows shared-memory compatibility, then the demo fallback
- `native_bridge`: only try `native/lmu_bridge/build/lmu_bridge.dll`
- `shared_memory`: only try the Windows named shared-memory reader
- `demo`: disable all real adapters

## Why the adapter is split this way

Le Mans Ultimate added a SharedMemory header file in the support folder for its newer shared-memory implementation, and later updates added more shared-memory telemetry parameters. The official support hub also warns that plugins can cause crashes, so the app keeps a safe fallback path instead of hard-failing when a plugin or bridge is missing.

## Environment variables

```
LMU_COACH_LIVE_MODE=auto
LMU_COACH_SHARED_MEMORY_PREFIX=rFactor2SMMP_
LMU_COACH_SHARED_MEMORY_TELEMETRY_NAME=rFactor2SMMP_Telemetry
LMU_COACH_SHARED_MEMORY_SCORING_NAME=rFactor2SMMP_Scoring
LMU_COACH_NATIVE_BRIDGE_PATH=C:\path\to\lmu_bridge.dll
LMU_COACH_WEBSOCKET_LIVE_HZ=10
```

## What works now without compiling

On Windows, the backend will try to open the named shared memory maps and read:

- telemetry: speed, throttle, brake, steering, gear, lap number
- scoring: player vehicle, lap distance, best lap, last lap

The app then projects the real lap progress onto the Imola reference line so the car dot follows your real position around the lap.

## What still needs your local LMU installation

To fully lock onto the official LMU shared-memory implementation, use the header from your local LMU Support folder and replace the native bridge stub implementation.
