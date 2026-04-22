export type Lap = {
  lap_index: number;
  lap_time_s: number | null;
  max_speed_kph: number | null;
  avg_speed_kph: number | null;
  notes: string[];
};

export type CoachingSuggestion = {
  corner_id: string | null;
  severity: string;
  title: string;
  detail: string;
  expected_gain_s: number;
  confidence: number;
};

export type AnalyzeTelemetryResponse = {
  source_file: string;
  tables: string[];
  inferred_channels: Record<string, string | null>;
  laps: Lap[];
  suggestions: CoachingSuggestion[];
  debug: Record<string, unknown>;
};

export type TrackPayload = {
  track_id: string;
  track: {
    display_name: string;
    short_name?: string;
    length_m?: number;
    status?: string;
    country?: string;
    assets?: {
      map_svg_file?: string;
      map_svg_json?: string;
      spectator_map_png?: string;
    };
  };
  corners: Array<{
    id: string;
    name: string;
    sequence: number;
    type: string;
    distance_hint_m: number;
    progress: number;
    x: number;
    y: number;
  }>;
  reference_line: {
    version: number;
    source: string;
    polyline: Array<{ x: number; y: number }>;
    brake_markers: Array<{ corner_id: string; progress: number }>;
    throttle_zones: Array<{ from_progress: number; to_progress: number }>;
    sectors: Array<{ id: string; name: string; start_progress: number; end_progress: number }>;
  };
  coach_rules: {
    cards?: Array<{ corner_id: string; title: string; tip: string; type: string }>;
  };
  map_svg?: {
    version: number;
    source: string;
    view_box: [number, number, number, number];
    path_d: string;
    stroke_track_outer: number;
    stroke_track_inner: number;
    start_finish?: { x1: number; y1: number; x2: number; y2: number };
  } | null;
};

export type LiveTelemetrySnapshot = {
  mode: string;
  source: string;
  status: string | null;
  track_id: string;
  track_name: string | null;
  progress: number;
  x: number;
  y: number;
  speed_kph: number;
  throttle_pct: number;
  brake_pct: number;
  steering_deg: number;
  gear: number;
  current_lap: number;
  lap_delta_s: number;
  best_lap_s: number | null;
  last_lap_s: number | null;
  current_corner_id: string | null;
  timestamp_ms: number;
};

const API_ROOT = "http://127.0.0.1:8080";
const WS_ROOT = "ws://127.0.0.1:8080/telemetry/live/ws";

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function analyzeLatestTelemetry(): Promise<AnalyzeTelemetryResponse> {
  return getJson<AnalyzeTelemetryResponse>("/telemetry/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function loadTrack(trackId: string): Promise<TrackPayload> {
  return getJson<TrackPayload>(`/tracks/${trackId}`);
}

export async function getLiveTelemetry(): Promise<LiveTelemetrySnapshot> {
  return getJson<LiveTelemetrySnapshot>("/telemetry/live");
}

export function createLiveTelemetrySocket(onMessage: (snapshot: LiveTelemetrySnapshot) => void, onError?: () => void): WebSocket {
  const socket = new WebSocket(WS_ROOT);
  socket.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data) as LiveTelemetrySnapshot);
    } catch {
      onError?.();
    }
  };
  socket.onerror = () => onError?.();
  return socket;
}
