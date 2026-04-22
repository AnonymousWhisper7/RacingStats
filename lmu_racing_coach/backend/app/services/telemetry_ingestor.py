from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from app.domain.models import TelemetryFile
from app.services.lmu_locator import LMULocator


class TelemetryIngestor:
    def __init__(self) -> None:
        self.locator = LMULocator()

    def scan(self) -> tuple[Path | None, list[TelemetryFile]]:
        telemetry_dir = self.locator.detect_telemetry_dir()
        if telemetry_dir is None:
            return None, []

        files: list[TelemetryFile] = []
        for file_path in sorted(telemetry_dir.rglob("*.duckdb"), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = file_path.stat()
            files.append(
                TelemetryFile(
                    path=file_path,
                    size_bytes=stat.st_size,
                    modified_ts=stat.st_mtime,
                )
            )
        return telemetry_dir, files

    def inspect(self, file_path: Path) -> TelemetryFile:
        if not file_path.exists():
            raise FileNotFoundError(file_path)

        stat = file_path.stat()
        tables, schema = self._read_schema(file_path)
        return TelemetryFile(
            path=file_path,
            size_bytes=stat.st_size,
            modified_ts=stat.st_mtime,
            tables=tables,
            schema=schema,
        )

    def _read_schema(self, file_path: Path) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
        con = duckdb.connect(database=str(file_path), read_only=True)
        try:
            table_rows = con.execute("SHOW TABLES").fetchall()
            tables = [row[0] for row in table_rows]
            schema: dict[str, list[dict[str, Any]]] = {}
            for table in tables:
                desc_rows = con.execute(f"DESCRIBE {self._quote_identifier(table)}").fetchall()
                schema[table] = [
                    {
                        "column": row[0],
                        "type": row[1],
                        "null": row[2],
                        "key": row[3],
                        "default": row[4],
                        "extra": row[5],
                    }
                    for row in desc_rows
                ]
            return tables, schema
        finally:
            con.close()

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'
