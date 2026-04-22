import { useEffect, useMemo, useState } from "react";
import {
  analyzeLatestTelemetry,
  createLiveTelemetrySocket,
  getLiveTelemetry,
  loadTrack,
  type AnalyzeTelemetryResponse,
  type CoachingSuggestion,
  type Lap,
  type LiveTelemetrySnapshot,
  type TrackPayload,
} from "./api";

type DashboardState = {
  telemetry: AnalyzeTelemetryResponse | null;
  track: TrackPayload | null;
  live: LiveTelemetrySnapshot | null;
  error: string | null;
  loading: boolean;
};

const pageStyle: React.CSSProperties = {
  minHeight: "100vh",
  background: "radial-gradient(circle at top, #1b2333 0%, #0d1117 35%, #090b10 100%)",
  color: "#eef2ff",
  fontFamily: "Inter, Arial, sans-serif",
  padding: 24,
};

const panelStyle: React.CSSProperties = {
  background: "rgba(14, 19, 28, 0.88)",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 20,
  boxShadow: "0 20px 50px rgba(0,0,0,0.28)",
  backdropFilter: "blur(8px)",
};

export function App() {
  const [state, setState] = useState<DashboardState>({
    telemetry: null,
    track: null,
    live: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    void (async () => {
      try {
        const [telemetry, track] = await Promise.all([
          analyzeLatestTelemetry().catch(() => null),
          loadTrack("imola"),
        ]);
        setState((current) => ({ ...current, telemetry, track, loading: false, error: null }));
      } catch (err) {
        setState((current) => ({
          ...current,
          loading: false,
          error: err instanceof Error ? err.message : "Unable to load dashboard",
        }));
      }
    })();
  }, []);

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | null = null;
    let polling: number | null = null;

    const runPolling = async () => {
      try {
        const live = await getLiveTelemetry();
        if (!cancelled) {
          setState((current) => ({ ...current, live }));
        }
      } catch (err) {
        if (!cancelled) {
          setState((current) => ({ ...current, error: err instanceof Error ? err.message : "Live feed unavailable" }));
        }
      }
    };

    const startPollingFallback = () => {
      if (polling !== null) return;
      void runPolling();
      polling = window.setInterval(() => {
        void runPolling();
      }, 250);
    };

    try {
      socket = createLiveTelemetrySocket(
        (live) => {
          if (!cancelled) {
            setState((current) => ({ ...current, live, error: current.error?.includes("Live feed") ? null : current.error }));
          }
        },
        () => {
          startPollingFallback();
        },
      );
    } catch {
      startPollingFallback();
    }

    return () => {
      cancelled = true;
      if (socket) socket.close();
      if (polling !== null) window.clearInterval(polling);
    };
  }, []);

  const metrics = useMemo(() => buildMetrics(state.telemetry, state.live), [state.telemetry, state.live]);
  const sectorSummary = useMemo(() => buildSectorSummary(state.telemetry, state.live), [state.telemetry, state.live]);

  return (
    <main style={pageStyle}>
      <section
        style={{
          ...panelStyle,
          padding: 24,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 20,
          marginBottom: 24,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div style={{ color: "#8fb9ff", fontSize: 13, letterSpacing: 1.8, textTransform: "uppercase", marginBottom: 10 }}>
            Le Mans Ultimate Coach
          </div>
          <h1 style={{ margin: 0, fontSize: 38 }}>Live race dashboard</h1>
          <p style={{ margin: "10px 0 0", color: "#b8c1d9", maxWidth: 820, lineHeight: 1.5 }}>
            Live map, lap widgets, and coaching cards are now part of the UI. The map uses a demo/live fallback feed today, and it is ready to be swapped with the native LMU shared-memory bridge later.
          </p>
        </div>
        <div style={{ display: "grid", gap: 10, minWidth: 260 }}>
          <StatusChip label="Track" value={state.track?.track.short_name ?? "Imola"} />
          <StatusChip label="Feed" value={state.live ? `${state.live.mode} · ${state.live.source}` : (state.loading ? "Loading" : "Offline")} />
          <StatusChip label="Telemetry source" value={state.telemetry ? trimPath(state.telemetry.source_file) : "No LMU file yet"} subtle />
          <StatusChip label="Live status" value={state.live?.status ?? "Waiting for live feed"} subtle />
        </div>
      </section>

      {state.error && (
        <section style={{ ...panelStyle, padding: 16, marginBottom: 24, borderColor: "rgba(248,113,113,0.45)", color: "#fecaca" }}>
          {state.error}
        </section>
      )}

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(460px, 1.45fr) minmax(400px, 0.95fr)",
          gap: 24,
          alignItems: "start",
        }}
      >
        <div style={{ display: "grid", gap: 24 }}>
          <TrackMapPanel track={state.track} live={state.live} />
          <TelemetryBars live={state.live} />
          <CoachCards telemetry={state.telemetry} track={state.track} />
        </div>

        <div style={{ display: "grid", gap: 24 }}>
          <MetricGrid metrics={metrics} />
          <LapSummaryPanel telemetry={state.telemetry} />
          <SectorWidget sectors={sectorSummary} />
          <ChannelPanel telemetry={state.telemetry} />
        </div>
      </section>
    </main>
  );
}

function TrackMapPanel({ track, live }: { track: TrackPayload | null; live: LiveTelemetrySnapshot | null }) {
  const polyline = track?.reference_line.polyline ?? [];
  const corners = track?.corners ?? [];
  const currentCorner = corners.find((corner) => corner.id === live?.current_corner_id) ?? null;
  const points = polyline.map((point) => `${point.x * 1000},${point.y * 800}`).join(" ");
  const mapSvg = track?.map_svg ?? null;
  const backgroundMap = track?.track.assets?.spectator_map_png ?? null;
  const dotX = (live?.x ?? polyline[0]?.x ?? 0.5) * 1000;
  const dotY = (live?.y ?? polyline[0]?.y ?? 0.5) * 800;

  return (
    <section style={{ ...panelStyle, padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18, gap: 16, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 13, color: "#8fb9ff", textTransform: "uppercase", letterSpacing: 1.6 }}>Live map</div>
          <h2 style={{ margin: "8px 0 6px", fontSize: 28 }}>{track?.track.display_name ?? "Imola"}</h2>
          <div style={{ color: "#b8c1d9" }}>
            Current corner: <strong style={{ color: "#f8fafc" }}>{currentCorner?.name ?? "Loading…"}</strong>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Pill label="Lap" value={String(live?.current_lap ?? "—")} />
          <Pill label="Gear" value={live ? `G${live.gear}` : "—"} />
          <Pill label="Delta" value={live ? formatDelta(live.lap_delta_s) : "—"} accent={live ? live.lap_delta_s <= 0 : false} />
        </div>
      </div>
      <div
        style={{
          background: "linear-gradient(180deg, rgba(59,130,246,0.08), rgba(2,6,23,0.1))",
          borderRadius: 24,
          overflow: "hidden",
          position: "relative",
          minHeight: 560,
        }}
      >
        {backgroundMap ? (
          <img
            src={backgroundMap}
            alt="Imola spectator map reference"
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              opacity: 0.34,
              filter: "saturate(0.9) contrast(1.05)",
            }}
          />
        ) : null}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(180deg, rgba(2,6,23,0.18), rgba(2,6,23,0.34))",
          }}
        />
        <svg viewBox="0 0 1000 800" style={{ width: "100%", height: 560, display: "block", position: "relative", zIndex: 1 }}
          {[...Array(12)].map((_, idx) => (
            <line key={`v-${idx}`} x1={idx * 90 + 5} y1={0} x2={idx * 90 + 5} y2={800} stroke="rgba(148,163,184,0.08)" />
          ))}
          {[...Array(8)].map((_, idx) => (
            <line key={`h-${idx}`} x1={0} y1={idx * 100 + 8} x2={1000} y2={idx * 100 + 8} stroke="rgba(148,163,184,0.08)" />
          ))}
          {mapSvg?.path_d ? (
            <>
              <path d={mapSvg.path_d} fill="none" stroke="rgba(148,163,184,0.22)" strokeWidth={mapSvg.stroke_track_outer ?? 34} strokeLinecap="round" strokeLinejoin="round" />
              <path d={mapSvg.path_d} fill="none" stroke="rgba(96,165,250,0.95)" strokeWidth={mapSvg.stroke_track_inner ?? 12} strokeLinecap="round" strokeLinejoin="round" />
              {mapSvg.start_finish ? <line x1={mapSvg.start_finish.x1} y1={mapSvg.start_finish.y1} x2={mapSvg.start_finish.x2} y2={mapSvg.start_finish.y2} stroke="#F8FAFC" strokeWidth={4} strokeLinecap="round" /> : null}
            </>
          ) : (
            <>
              <polyline points={points} fill="none" stroke="rgba(148,163,184,0.22)" strokeWidth={34} strokeLinecap="round" strokeLinejoin="round" />
              <polyline points={points} fill="none" stroke="rgba(96,165,250,0.95)" strokeWidth={12} strokeLinecap="round" strokeLinejoin="round" />
            </>
          )}
          {(track?.reference_line.brake_markers ?? []).map((marker) => {
            const corner = corners.find((item) => item.id === marker.corner_id);
            if (!corner) return null;
            return (
              <g key={marker.corner_id}>
                <circle cx={corner.x * 1000} cy={corner.y * 800} r={16} fill="rgba(239,68,68,0.18)" stroke="rgba(248,113,113,0.75)" strokeWidth={2} />
                <text x={corner.x * 1000 + 24} y={corner.y * 800 + 6} fill="#fecaca" fontSize="16" fontFamily="Inter, Arial, sans-serif">
                  Brake
                </text>
              </g>
            );
          })}
          {corners.map((corner) => (
            <g key={corner.id}>
              <circle
                cx={corner.x * 1000}
                cy={corner.y * 800}
                r={corner.id === live?.current_corner_id ? 13 : 9}
                fill={corner.id === live?.current_corner_id ? "#fde68a" : "#dbeafe"}
                stroke={corner.id === live?.current_corner_id ? "#f59e0b" : "#60a5fa"}
                strokeWidth={2}
              />
              <text x={(corner.label_x ?? corner.x) * 1000} y={(corner.label_y ?? corner.y) * 800} fill="#cbd5e1" fontSize="16" fontFamily="Inter, Arial, sans-serif">
                {corner.name}
              </text>
            </g>
          ))}
          <circle cx={dotX} cy={dotY} r={18} fill="rgba(34,197,94,0.22)" />
          <circle cx={dotX} cy={dotY} r={10} fill="#22c55e" />
          <text x={dotX + 18} y={dotY - 18} fill="#BBF7D0" fontSize="15" fontFamily="Inter, Arial, sans-serif">
            YOU
          </text>
        </svg>
      </div>
      <div style={{ marginTop: 12, color: "#94a3b8", fontSize: 13 }}>
        Background reference uses the Imola spectator map image. The bright blue track path, corner anchors, and live car dot remain our own app overlays.
      </div>
    </section>
  );
}

function TelemetryBars({ live }: { live: LiveTelemetrySnapshot | null }) {
  const bars = [
    { label: "Throttle", value: live?.throttle_pct ?? 0, color: "linear-gradient(90deg, #22c55e, #4ade80)" },
    { label: "Brake", value: live?.brake_pct ?? 0, color: "linear-gradient(90deg, #ef4444, #f97316)" },
    { label: "Steering load", value: Math.min(100, Math.abs(live?.steering_deg ?? 0) * 3.5), color: "linear-gradient(90deg, #60a5fa, #a78bfa)" },
  ];

  return (
    <section style={{ ...panelStyle, padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 24 }}>Live inputs</h2>
        <div style={{ color: "#94a3b8" }}>{live ? `${live.speed_kph.toFixed(1)} kph` : "No signal"}</div>
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        {bars.map((bar) => (
          <div key={bar.label}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, color: "#dbeafe" }}>
              <span>{bar.label}</span>
              <strong>{bar.value.toFixed(0)}%</strong>
            </div>
            <div style={{ height: 14, borderRadius: 999, background: "rgba(148,163,184,0.16)", overflow: "hidden" }}>
              <div style={{ width: `${bar.value}%`, height: "100%", background: bar.color, transition: "width 0.35s ease" }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CoachCards({ telemetry, track }: { telemetry: AnalyzeTelemetryResponse | null; track: TrackPayload | null }) {
  const cards = telemetry?.suggestions?.length
    ? telemetry.suggestions
    : (track?.coach_rules.cards ?? []).map<CoachingSuggestion>((card) => ({
        corner_id: card.corner_id,
        severity: "info",
        title: card.title,
        detail: card.tip,
        expected_gain_s: 0.05,
        confidence: 0.5,
      }));

  return (
    <section style={{ ...panelStyle, padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18, gap: 16, flexWrap: "wrap" }}>
        <div>
          <div style={{ color: "#8fb9ff", fontSize: 13, textTransform: "uppercase", letterSpacing: 1.5 }}>Coaching</div>
          <h2 style={{ margin: "8px 0 0", fontSize: 24 }}>Priority cards for the next lap</h2>
        </div>
        <div style={{ color: "#94a3b8" }}>Top 3 actions only, to keep the coaching usable mid-session.</div>
      </div>
      <div style={{ display: "grid", gap: 14 }}>
        {cards.map((suggestion) => (
          <article
            key={`${suggestion.corner_id}-${suggestion.title}`}
            style={{
              borderRadius: 18,
              border: `1px solid ${severityBorder(suggestion.severity)}`,
              background: "linear-gradient(180deg, rgba(15,23,42,0.9), rgba(10,15,24,0.9))",
              padding: 18,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
              <div>
                <div style={{ color: severityText(suggestion.severity), fontSize: 13, textTransform: "uppercase", letterSpacing: 1.2 }}>
                  {suggestion.severity} priority {suggestion.corner_id ? `· ${suggestion.corner_id.toUpperCase()}` : ""}
                </div>
                <h3 style={{ margin: "8px 0 0", fontSize: 21 }}>{suggestion.title}</h3>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <Pill label="Expected gain" value={`+${suggestion.expected_gain_s.toFixed(2)}s`} accent />
                <Pill label="Confidence" value={`${Math.round(suggestion.confidence * 100)}%`} />
              </div>
            </div>
            <p style={{ margin: "12px 0 0", color: "#d7def0", lineHeight: 1.6 }}>{suggestion.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function MetricGrid({ metrics }: { metrics: Array<{ label: string; value: string; helper: string; accent?: boolean }> }) {
  return (
    <section style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 16 }}>
      {metrics.map((metric) => (
        <article key={metric.label} style={{ ...panelStyle, padding: 18 }}>
          <div style={{ color: "#8fb9ff", fontSize: 13, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 10 }}>{metric.label}</div>
          <div style={{ fontSize: 34, fontWeight: 700, color: metric.accent ? "#86efac" : "#f8fafc" }}>{metric.value}</div>
          <div style={{ color: "#94a3b8", marginTop: 8 }}>{metric.helper}</div>
        </article>
      ))}
    </section>
  );
}

function LapSummaryPanel({ telemetry }: { telemetry: AnalyzeTelemetryResponse | null }) {
  const laps = (telemetry?.laps ?? []).slice(-5).reverse();
  return (
    <section style={{ ...panelStyle, padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 24 }}>Lap summary</h2>
        <div style={{ color: "#94a3b8" }}>{telemetry?.laps.length ?? 0} laps loaded</div>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {laps.length === 0 && <div style={{ color: "#94a3b8" }}>No LMU telemetry loaded yet. The layout still renders so you can continue building the UI.</div>}
        {laps.map((lap) => (
          <LapRow key={lap.lap_index} lap={lap} />
        ))}
      </div>
    </section>
  );
}

function LapRow({ lap }: { lap: Lap }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "100px 1fr auto",
        gap: 14,
        padding: 14,
        borderRadius: 16,
        background: "rgba(15, 23, 42, 0.65)",
        border: "1px solid rgba(148, 163, 184, 0.12)",
        alignItems: "center",
      }}
    >
      <div>
        <div style={{ color: "#8fb9ff", fontSize: 12, textTransform: "uppercase", letterSpacing: 1.2 }}>Lap</div>
        <div style={{ fontSize: 24, fontWeight: 700 }}>{lap.lap_index}</div>
      </div>
      <div>
        <div style={{ fontSize: 22, fontWeight: 700 }}>{lap.lap_time_s ? formatLapTime(lap.lap_time_s) : "—"}</div>
        <div style={{ color: "#94a3b8", marginTop: 4 }}>
          Avg {lap.avg_speed_kph?.toFixed(1) ?? "—"} kph · Max {lap.max_speed_kph?.toFixed(1) ?? "—"} kph
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
        {(lap.notes.length ? lap.notes : ["timed lap"]).map((note) => (
          <span key={note} style={{ padding: "7px 10px", borderRadius: 999, background: "rgba(59,130,246,0.14)", color: "#bfdbfe", fontSize: 12 }}>
            {note}
          </span>
        ))}
      </div>
    </div>
  );
}

function SectorWidget({ sectors }: { sectors: Array<{ name: string; delta: string; color: string; note: string }> }) {
  return (
    <section style={{ ...panelStyle, padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 24 }}>Sector widgets</h2>
        <div style={{ color: "#94a3b8" }}>Live demo deltas</div>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {sectors.map((sector) => (
          <div key={sector.name} style={{ padding: 14, borderRadius: 16, background: "rgba(15,23,42,0.62)", border: "1px solid rgba(148,163,184,0.12)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
              <strong>{sector.name}</strong>
              <span style={{ color: sector.color, fontWeight: 700 }}>{sector.delta}</span>
            </div>
            <div style={{ color: "#94a3b8", marginTop: 6 }}>{sector.note}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ChannelPanel({ telemetry }: { telemetry: AnalyzeTelemetryResponse | null }) {
  return (
    <section style={{ ...panelStyle, padding: 22 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <h2 style={{ margin: 0, fontSize: 24 }}>Mapped telemetry channels</h2>
        <div style={{ color: "#94a3b8" }}>{telemetry ? "Auto-inferred from latest file" : "Waiting for LMU file"}</div>
      </div>
      <div style={{ display: "grid", gap: 10 }}>
        {Object.entries(telemetry?.inferred_channels ?? {
          lap: null,
          speed: null,
          time: null,
          brake: null,
          throttle: null,
          steer: null,
          distance: null,
        }).map(([key, value]) => (
          <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "12px 14px", borderRadius: 14, background: "rgba(15,23,42,0.55)" }}>
            <span style={{ textTransform: "capitalize" }}>{key}</span>
            <code style={{ color: value ? "#bfdbfe" : "#94a3b8" }}>{value ?? "not mapped yet"}</code>
          </div>
        ))}
      </div>
    </section>
  );
}

function StatusChip({ label, value, subtle = false }: { label: string; value: string; subtle?: boolean }) {
  return (
    <div style={{ padding: "12px 14px", borderRadius: 14, background: subtle ? "rgba(15,23,42,0.45)" : "rgba(59,130,246,0.12)", border: "1px solid rgba(148,163,184,0.12)" }}>
      <div style={{ color: "#8fb9ff", fontSize: 12, textTransform: "uppercase", letterSpacing: 1.2 }}>{label}</div>
      <div style={{ marginTop: 4 }}>{value}</div>
    </div>
  );
}

function Pill({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div style={{ padding: "10px 12px", borderRadius: 999, background: accent ? "rgba(34,197,94,0.14)" : "rgba(148,163,184,0.12)", color: accent ? "#bbf7d0" : "#dbeafe", fontSize: 13 }}>
      <strong>{label}:</strong> {value}
    </div>
  );
}

function buildMetrics(telemetry: AnalyzeTelemetryResponse | null, live: LiveTelemetrySnapshot | null) {
  const timedLaps = (telemetry?.laps ?? []).filter((lap) => lap.lap_time_s !== null);
  const bestLap = timedLaps.length ? Math.min(...timedLaps.map((lap) => lap.lap_time_s as number)) : null;
  const lastLap = timedLaps.length ? timedLaps[timedLaps.length - 1]?.lap_time_s ?? null : null;
  const avgTopSpeed = telemetry?.laps.length
    ? telemetry.laps.reduce((acc, lap) => acc + (lap.max_speed_kph ?? 0), 0) / telemetry.laps.length
    : null;

  return [
    { label: "Speed", value: live ? `${live.speed_kph.toFixed(1)} kph` : "—", helper: "Instant speed from the live feed" },
    { label: "Best lap", value: bestLap ? formatLapTime(bestLap) : "—", helper: "Best detected timed lap" },
    { label: "Last lap", value: lastLap ? formatLapTime(lastLap) : "—", helper: "Latest timed lap" },
    { label: "Lap delta", value: live ? formatDelta(live.lap_delta_s) : "—", helper: "Live delta against the rolling demo reference", accent: live ? live.lap_delta_s <= 0 : false },
    { label: "Top speed avg", value: avgTopSpeed ? `${avgTopSpeed.toFixed(1)} kph` : "—", helper: "Average max speed over loaded laps" },
    { label: "Current corner", value: live?.current_corner_id?.toUpperCase() ?? "—", helper: "Corner marker nearest to the live car dot" },
  ];
}

function buildSectorSummary(telemetry: AnalyzeTelemetryResponse | null, live: LiveTelemetrySnapshot | null) {
  const delta = live?.lap_delta_s ?? 0;
  const laps = telemetry?.laps ?? [];
  const timed = laps.filter((lap) => lap.lap_time_s !== null);
  const roughBase = timed.length ? (timed.reduce((acc, lap) => acc + (lap.lap_time_s ?? 0), 0) / timed.length) : 104.8;
  return [
    { name: "Sector 1", delta: formatDelta(delta * 0.55), color: delta <= 0 ? "#86efac" : "#fca5a5", note: `Tamburello to Tosa · reference ${formatLapTime(roughBase / 3.02)}` },
    { name: "Sector 2", delta: formatDelta(delta * -0.15), color: delta <= 0 ? "#fca5a5" : "#86efac", note: "Piratella to Acque Minerali · watch stability" },
    { name: "Sector 3", delta: formatDelta(delta * 0.6), color: delta <= 0 ? "#86efac" : "#fca5a5", note: "Variante Alta to Rivazza · exit speed sensitive" },
  ];
}

function formatLapTime(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds - minutes * 60;
  return `${minutes}:${remaining.toFixed(3).padStart(6, "0")}`;
}

function formatDelta(seconds: number): string {
  return `${seconds <= 0 ? "-" : "+"}${Math.abs(seconds).toFixed(3)}s`;
}

function trimPath(path: string): string {
  const normalized = path.replaceAll("\\", "/");
  const parts = normalized.split("/");
  return parts.slice(Math.max(0, parts.length - 3)).join("/");
}

function severityBorder(severity: string): string {
  if (severity === "high") return "rgba(248,113,113,0.40)";
  if (severity === "medium") return "rgba(251,191,36,0.34)";
  return "rgba(96,165,250,0.24)";
}

function severityText(severity: string): string {
  if (severity === "high") return "#fda4af";
  if (severity === "medium") return "#fde68a";
  return "#93c5fd";
}
