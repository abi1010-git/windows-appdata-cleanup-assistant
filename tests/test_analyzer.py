from __future__ import annotations

import time
from pathlib import Path

from app.analyzer import build_finding, classify_path, explanation_for
from app.installed_apps import InstalledAppInventory
from app.models import CATEGORY_CACHE, CATEGORY_LEFTOVER, CATEGORY_TEMP, RISK_SAFE


def test_classify_cache_and_temp_paths() -> None:
    assert classify_path(Path("Discord") / "Cache")[0] == CATEGORY_CACHE
    assert classify_path(Path("SomeApp") / "Temp")[0] == CATEGORY_TEMP


def test_build_finding_marks_low_risk_cache_cleanup_candidate(tmp_path: Path) -> None:
    cache_dir = tmp_path / "Discord" / "Cache"
    cache_dir.mkdir(parents=True)
    inventory = InstalledAppInventory(app_names={"Discord"})

    finding = build_finding(
        path=cache_dir,
        size_bytes=128 * 1024 * 1024,
        last_modified=time.time() - 40 * 24 * 3600,
        source_root=tmp_path,
        inventory=inventory,
    )

    assert finding.category == CATEGORY_CACHE
    assert finding.detected_app == "Discord"
    assert finding.risk == RISK_SAFE
    assert finding.cleanup_eligible is True


def test_leftover_app_data_when_app_not_installed(tmp_path: Path) -> None:
    app_dir = tmp_path / "AppData" / "Roaming" / "OldChat"
    app_dir.mkdir(parents=True)
    inventory = InstalledAppInventory(app_names={"Discord"})

    finding = build_finding(
        path=app_dir,
        size_bytes=512 * 1024 * 1024,
        last_modified=time.time() - 300 * 24 * 3600,
        source_root=tmp_path,
        inventory=inventory,
    )

    assert finding.category == CATEGORY_LEFTOVER
    assert finding.cleanup_eligible is False
    assert "not appear" in finding.explanation


def test_explanation_mentions_cleanup_eligibility() -> None:
    explanation = explanation_for(
        path="Cache",
        size_bytes=1024**3,
        age_days=365,
        category=CATEGORY_CACHE,
        detected_app="Discord",
        is_installed=False,
        cleanup_eligible=True,
    )

    assert "Discord" in explanation
    assert "Estimated recoverable storage: 1.0 GB" in explanation
    assert "eligible" in explanation
