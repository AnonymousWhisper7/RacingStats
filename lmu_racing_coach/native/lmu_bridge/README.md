# Native LMU bridge

This folder is the optional path for a production bridge compiled against the official LMU shared-memory header that Studio 397 / LMU places in the Support folder.

## What is already usable now

The backend already includes a Windows shared-memory compatibility adapter that tries to open the named memory maps exposed by the rFactor2-style shared-memory ecosystem. If that works on your machine, you can get a real moving car dot without compiling anything.

## When to use the native bridge

Use this bridge when you want to target the official LMU shared-memory header and exact structures from your local game build.

## Expected DLL path

`native/lmu_bridge/build/lmu_bridge.dll`

The Python backend will auto-load that DLL when `LMU_COACH_LIVE_MODE=auto` or `LMU_COACH_LIVE_MODE=native_bridge`.
