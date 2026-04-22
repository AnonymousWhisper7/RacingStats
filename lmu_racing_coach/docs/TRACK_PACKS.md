# Track packs

Each track pack can expose:
- `track.json` for metadata
- `corners.json` for corner anchors and labels
- `reference_line.json` for progress mapping
- `map_svg.json` for an internal UI-safe SVG redraw
- `map.svg` as a standalone asset

The frontend should prefer `map_svg.path_d` when available and fall back to `reference_line.polyline`.

A track can also expose `track.assets.spectator_map_png` for a low-opacity visual reference background under the vector overlay.
Use this as a reference layer only; keep the interactive path, markers, and labels in your own overlay.
