from __future__ import annotations

from pathlib import Path

import pytest

try:
    from PyQt6.QtWidgets import QApplication
except Exception:  # pragma: no cover - only used when GUI deps are unavailable.
    QApplication = None

from app.database import StorageDatabase


@pytest.mark.skipif(QApplication is None, reason="PyQt6 is not installed")
def test_main_window_constructs(tmp_path: Path) -> None:
    from app.gui import create_window

    app = QApplication.instance() or QApplication([])
    window = create_window(StorageDatabase(tmp_path / "storage.sqlite3"))

    assert window.windowTitle() == "Storage Detective"
    assert window.dashboard_page.scan_button.text() == "Start Scan"
    assert window.results_page.table.columnCount() == 7
    window.close()
