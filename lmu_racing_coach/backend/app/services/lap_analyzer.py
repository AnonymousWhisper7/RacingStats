from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from app.schemas.telemetry import AnalyzedLap


class LapAnalyzer:
    CANDIDATE_COLUMN_MAP: dict[str, list[str]] = {
        "lap": ["lap", "lapnumber", "lap_num", "lap_number"],
        "speed": ["speed", "vehicle_speed", "speedkph", "speed_kph"],
        "time": ["time", "sessiontime", "lap_time", "elapsed_time"],
        "brake": ["brake", "brake_pos", "brakepos"],
        "throttle": ["throttle", "throttle_pos", "throttlepos"],
        "steer": ["steer", "steering", "steeringwheelangle"],
        "distance": ["lapdist", "distance", "lap_distance", "trackpos"],
    }

    def analyze(self, file_path: Path) -> tuple[list[AnalyzedLap], dict[str, str | None], dict[str, Any]]:
        con = duckdb.connect(database=str(file_path), read_only=True)
        try:
            tables = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
            schemas = {table: con.execute(f"DESCRIBE {self._quote_identifier(table)}").fetchall() for table in tables}
            columns_by_table = {table: [str(row[0]) for row in rows] for table, rows in schemas.items()}

            selected_table = self._pick_best_table(columns_by_table)
            if not selected_table:
                return [], {key: None for key in self.CANDIDATE_COLUMN_MAP}, {"reason": "no_table_match"}

            inferred = self._infer_columns(columns_by_table[selected_table])
            lap_col = inferred.get("lap")
            speed_col = inferred.get("speed")
            time_col = inferred.get("time")

            if not lap_col:
                return [], inferred, {"reason": "no_lap_column", "table": selected_table}

            select_parts = [f"{self._quote_identifier(lap_col)} AS lap_idx"]
            if speed_col:
                select_parts.append(f"AVG({self._quote_identifier(speed_col)}) AS avg_speed")
                select_parts.append(f"MAX({self._quote_identifier(speed_col)}) AS max_speed")
            if time_col:
                select_parts.append(f"MAX({self._quote_identifier(time_col)}) - MIN({self._quote_identifier(time_col)}) AS lap_time")

            query = (
                f"SELECT {', '.join(select_parts)} "
                f"FROM {self._quote_identifier(selected_table)} "
                "GROUP BY lap_idx "
                "ORDER BY lap_idx"
            )
            rows = con.execute(query).fetchall()
            laps: list[AnalyzedLap] = []
            for row in rows:
                idx = int(row[0]) if row[0] is not None else -1
                lap_time = float(row[-1]) if time_col and row[-1] is not None else None
                if speed_col and time_col:
                    avg_speed = float(row[1]) if row[1] is not None else None
                    max_speed = float(row[2]) if row[2] is not None else None
                elif speed_col:
                    avg_speed = float(row[1]) if row[1] is not None else None
                    max_speed = float(row[2]) if len(row) > 2 and row[2] is not None else None
                else:
                    avg_speed = None
                    max_speed = None

                laps.append(
                    AnalyzedLap(
                        lap_index=idx,
                        lap_time_s=lap_time,
                        max_speed_kph=max_speed,
                        avg_speed_kph=avg_speed,
                        notes=[],
                    )
                )

            return laps, inferred, {"table": selected_table, "query": query}
        finally:
            con.close()

    def _pick_best_table(self, columns_by_table: dict[str, list[str]]) -> str | None:
        best_table = None
        best_score = -1
        for table, columns in columns_by_table.items():
            inferred = self._infer_columns(columns)
            score = sum(1 for value in inferred.values() if value)
            if score > best_score:
                best_table = table
                best_score = score
        return best_table

    def _infer_columns(self, columns: list[str]) -> dict[str, str | None]:
        lowered = {col.lower().replace(" ", "").replace("-", "").replace("_", ""): col for col in columns}
        inferred: dict[str, str | None] = {}
        for semantic_name, candidates in self.CANDIDATE_COLUMN_MAP.items():
            inferred[semantic_name] = None
            for candidate in candidates:
                normalized = candidate.lower().replace(" ", "").replace("-", "").replace("_", "")
                if normalized in lowered:
                    inferred[semantic_name] = lowered[normalized]
                    break
        return inferred

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'
