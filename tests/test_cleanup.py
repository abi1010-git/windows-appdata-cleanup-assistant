from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from app.cleanup import CleanupError, CleanupManager
from app.models import CATEGORY_CACHE, Finding, RISK_REVIEW, RISK_SAFE, STATUS_CLEANED, STATUS_READY


def make_finding(path: Path, *, risk: str = RISK_SAFE, cleanup_eligible: bool = True) -> Finding:
    return Finding(
        path=str(path),
        name=path.name,
        size_bytes=42,
        last_modified=time.time(),
        category=CATEGORY_CACHE,
        detected_app="Example",
        is_installed=True,
        risk=risk,
        status=STATUS_READY,
        recommendation="Review, then clean.",
        explanation="Cache folder.",
        cleanup_eligible=cleanup_eligible,
        source_root=str(path.parent),
    )


def test_cleanup_requires_confirmation(tmp_path: Path) -> None:
    target = tmp_path / "Cache"
    target.mkdir()
    manager = CleanupManager([tmp_path])

    with pytest.raises(CleanupError, match="confirmation"):
        manager.move_to_recycle_bin(make_finding(target), confirmed=False)


def test_cleanup_blocks_review_risk(tmp_path: Path) -> None:
    target = tmp_path / "Cache"
    target.mkdir()
    manager = CleanupManager([tmp_path])

    with pytest.raises(CleanupError, match="not eligible"):
        manager.move_to_recycle_bin(make_finding(target, risk=RISK_REVIEW), confirmed=True)


def test_cleanup_uses_send2trash_and_updates_status(tmp_path: Path) -> None:
    target = tmp_path / "Cache"
    target.mkdir()
    manager = CleanupManager([tmp_path])
    finding = make_finding(target)

    with patch("app.cleanup.send2trash") as mocked_send:
        updated = manager.move_to_recycle_bin(finding, confirmed=True)

    mocked_send.assert_called_once_with(str(target))
    assert updated.status == STATUS_CLEANED
    assert updated.cleanup_eligible is False
