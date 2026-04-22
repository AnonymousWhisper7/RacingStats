from __future__ import annotations

from typing import Iterable

from app.domain.models import CoachingSuggestion
from app.schemas.telemetry import AnalyzedLap


class CoachingEngine:
    def build_suggestions(self, laps: Iterable[AnalyzedLap]) -> list[CoachingSuggestion]:
        lap_list = [lap for lap in laps if lap.lap_time_s is not None]
        if len(lap_list) < 2:
            return [
                CoachingSuggestion(
                    corner_id=None,
                    severity="info",
                    title="Collect more clean laps",
                    detail="The coach needs at least two timed laps to start producing meaningful comparative feedback.",
                    expected_gain_s=0.0,
                    confidence=0.35,
                )
            ]

        best = min(lap_list, key=lambda lap: lap.lap_time_s or float("inf"))
        latest = lap_list[-1]
        delta = (latest.lap_time_s or 0.0) - (best.lap_time_s or 0.0)

        suggestions: list[CoachingSuggestion] = []
        if delta > 0.35:
            suggestions.append(
                CoachingSuggestion(
                    corner_id="sector_focus",
                    severity="high",
                    title="Too much lap-to-lap variance",
                    detail=(
                        "Your latest lap is materially slower than your best reference. "
                        "Focus on braking consistency first before chasing later apex speed."
                    ),
                    expected_gain_s=round(min(delta * 0.55, 0.8), 3),
                    confidence=0.64,
                )
            )

        if latest.max_speed_kph and best.max_speed_kph and latest.max_speed_kph < best.max_speed_kph - 3.0:
            suggestions.append(
                CoachingSuggestion(
                    corner_id="exit_speed",
                    severity="medium",
                    title="Exit speed is probably leaving time on the table",
                    detail="Top speed is down versus your best lap, which usually points to compromised corner exits or earlier lift phases.",
                    expected_gain_s=0.12,
                    confidence=0.58,
                )
            )

        if latest.avg_speed_kph and best.avg_speed_kph and latest.avg_speed_kph < best.avg_speed_kph - 2.0:
            suggestions.append(
                CoachingSuggestion(
                    corner_id="minimum_speed",
                    severity="medium",
                    title="Corner minimum speeds look conservative",
                    detail="Average speed is below your benchmark. Start by checking the slow and medium-speed corners for over-braking.",
                    expected_gain_s=0.09,
                    confidence=0.56,
                )
            )

        if not suggestions:
            suggestions.append(
                CoachingSuggestion(
                    corner_id=None,
                    severity="info",
                    title="Session is trending in the right direction",
                    detail="Your latest lap is close to your current benchmark. Next step: unlock corner-specific analysis once distance/brake channels are mapped.",
                    expected_gain_s=0.05,
                    confidence=0.52,
                )
            )

        return suggestions[:3]
