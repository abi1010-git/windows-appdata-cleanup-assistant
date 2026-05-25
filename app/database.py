from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import DEFAULT_DB_PATH, AppSettings
from app.models import Finding, ScanResult, STATUS_IGNORED, utc_now_iso


class StorageDatabase:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS scan_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    finding_count INTEGER NOT NULL,
                    recoverable_bytes INTEGER NOT NULL,
                    errors_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_run_id INTEGER NOT NULL,
                    path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    last_modified REAL,
                    category TEXT NOT NULL,
                    detected_app TEXT,
                    is_installed INTEGER,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    cleanup_eligible INTEGER NOT NULL,
                    source_root TEXT NOT NULL,
                    reason_tags_json TEXT NOT NULL,
                    error TEXT,
                    FOREIGN KEY(scan_run_id) REFERENCES scan_runs(id)
                );

                CREATE TABLE IF NOT EXISTS ignored_paths (
                    path TEXT PRIMARY KEY,
                    ignored_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cleanup_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    finding_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    cleaned_at TEXT NOT NULL,
                    method TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL
                );
                """
            )

    def save_scan(self, result: ScanResult) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO scan_runs (started_at, completed_at, finding_count, recoverable_bytes, errors_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.started_at,
                    result.completed_at,
                    len(result.findings),
                    result.total_recoverable_bytes,
                    json.dumps(result.errors),
                ),
            )
            run_id = int(cursor.lastrowid)
            for finding in result.findings:
                finding.id = self._insert_finding(conn, run_id, finding)
            return run_id

    def _insert_finding(self, conn: sqlite3.Connection, run_id: int, finding: Finding) -> int:
        cursor = conn.execute(
            """
            INSERT INTO findings (
                scan_run_id, path, name, size_bytes, last_modified, category, detected_app, is_installed,
                risk, status, recommendation, explanation, cleanup_eligible, source_root,
                reason_tags_json, error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                finding.path,
                finding.name,
                finding.size_bytes,
                finding.last_modified,
                finding.category,
                finding.detected_app,
                _optional_bool_to_int(finding.is_installed),
                finding.risk,
                finding.status,
                finding.recommendation,
                finding.explanation,
                int(finding.cleanup_eligible),
                finding.source_root,
                json.dumps(finding.reason_tags),
                finding.error,
            ),
        )
        return int(cursor.lastrowid)

    def recent_findings(self, limit: int = 200) -> list[Finding]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM findings ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [finding_from_row(row) for row in rows]

    def scan_history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM scan_runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def mark_ignored(self, finding: Finding) -> None:
        finding.status = STATUS_IGNORED
        finding.cleanup_eligible = False
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ignored_paths (path, ignored_at) VALUES (?, ?)",
                (finding.path, utc_now_iso()),
            )
            conn.execute(
                "UPDATE findings SET status = ?, cleanup_eligible = 0 WHERE path = ?",
                (STATUS_IGNORED, finding.path),
            )

    def record_cleanup(self, finding: Finding) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO cleanup_events (finding_path, size_bytes, cleaned_at, method) VALUES (?, ?, ?, ?)",
                (finding.path, finding.size_bytes, utc_now_iso(), "send2trash"),
            )
            conn.execute(
                "UPDATE findings SET status = ?, cleanup_eligible = 0 WHERE path = ?",
                (finding.status, finding.path),
            )

    def ignored_paths(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT path FROM ignored_paths ORDER BY ignored_at DESC").fetchall()
        return [str(row["path"]) for row in rows]

    def load_settings(self) -> AppSettings:
        with self.connect() as conn:
            rows = conn.execute("SELECT key, value_json FROM settings").fetchall()
        values: dict[str, Any] = {}
        for row in rows:
            try:
                values[row["key"]] = json.loads(row["value_json"])
            except json.JSONDecodeError:
                continue
        return AppSettings.from_dict(values)

    def save_settings(self, settings: AppSettings) -> None:
        with self.connect() as conn:
            for key, value in settings.to_dict().items():
                conn.execute(
                    "INSERT OR REPLACE INTO settings (key, value_json) VALUES (?, ?)",
                    (key, json.dumps(value)),
                )


def finding_from_row(row: sqlite3.Row) -> Finding:
    payload = {
        "id": row["id"],
        "path": row["path"],
        "name": row["name"],
        "size_bytes": row["size_bytes"],
        "last_modified": row["last_modified"],
        "category": row["category"],
        "detected_app": row["detected_app"],
        "is_installed": _int_to_optional_bool(row["is_installed"]),
        "risk": row["risk"],
        "status": row["status"],
        "recommendation": row["recommendation"],
        "explanation": row["explanation"],
        "cleanup_eligible": bool(row["cleanup_eligible"]),
        "source_root": row["source_root"],
        "reason_tags": json.loads(row["reason_tags_json"] or "[]"),
        "error": row["error"],
    }
    return Finding.from_dict(payload)


def _optional_bool_to_int(value: bool | None) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _int_to_optional_bool(value: int | None) -> bool | None:
    if value is None:
        return None
    return bool(value)
