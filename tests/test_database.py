from __future__ import annotations

import time
from pathlib import Path

from app.config import AppSettings
from app.database import StorageDatabase
from app.models import CATEGORY_CACHE, Finding, RISK_SAFE, STATUS_IGNORED, STATUS_READY, ScanResult


def sample_finding(path: Path) -> Finding:
    return Finding(
        path=str(path),
        name=path.name,
        size_bytes=123,
        last_modified=time.time(),
        category=CATEGORY_CACHE,
        detected_app="Example",
        is_installed=True,
        risk=RISK_SAFE,
        status=STATUS_READY,
        recommendation="Clean after review.",
        explanation="Cache data.",
        cleanup_eligible=True,
        source_root=str(path.parent),
        reason_tags=["cache-marker"],
    )


def test_database_persists_scan_and_findings(tmp_path: Path) -> None:
    db = StorageDatabase(tmp_path / "storage.sqlite3")
    finding = sample_finding(tmp_path / "Cache")
    run_id = db.save_scan(ScanResult(findings=[finding], errors=["denied"]))

    assert run_id == 1
    rows = db.recent_findings()
    assert len(rows) == 1
    assert rows[0].path == finding.path
    assert db.scan_history()[0]["finding_count"] == 1


def test_database_settings_roundtrip(tmp_path: Path) -> None:
    db = StorageDatabase(tmp_path / "storage.sqlite3")
    settings = AppSettings(excluded_paths=["C:/Temp/Skip"], theme="light", scan_depth=3, min_folder_size_mb=10)

    db.save_settings(settings)
    loaded = db.load_settings()

    assert loaded.excluded_paths == ["C:/Temp/Skip"]
    assert loaded.theme == "light"
    assert loaded.scan_depth == 3
    assert loaded.min_folder_size_mb == 10


def test_database_mark_ignored(tmp_path: Path) -> None:
    db = StorageDatabase(tmp_path / "storage.sqlite3")
    finding = sample_finding(tmp_path / "Cache")
    db.save_scan(ScanResult(findings=[finding]))

    db.mark_ignored(finding)

    assert finding.status == STATUS_IGNORED
    assert finding.path in db.ignored_paths()
