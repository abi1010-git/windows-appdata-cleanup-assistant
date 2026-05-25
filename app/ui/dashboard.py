from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget

from app.models import ScanResult, format_bytes
from app.ui.widgets import SummaryCard, horizontal_cards, page_header


class DashboardPage(QWidget):
    scan_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.recoverable_card = SummaryCard("Recoverable Space", "0 B", "Cleanup candidates after safety checks")
        self.unused_card = SummaryCard("Unused App Data", "0", "Folders that may belong to removed apps")
        self.cache_card = SummaryCard("Cache Files", "0", "Cache/temp folders found")
        self.risk_card = SummaryCard("Risk Level", "Low", "Sensitive folders are never cleanup eligible")

        self.scan_button = QPushButton("Start Scan")
        self.scan_button.setObjectName("Primary")
        self.scan_button.clicked.connect(self.scan_requested.emit)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.status_label = QLabel("Ready to scan Windows app data locations.")
        self.status_label.setObjectName("Muted")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(18)
        layout.addWidget(
            page_header(
                "Dashboard",
                "Find stale app data, large caches, and temporary folders without permanently deleting anything.",
            )
        )
        layout.addWidget(
            horizontal_cards([self.recoverable_card, self.unused_card, self.cache_card, self.risk_card])
        )
        layout.addSpacing(4)
        layout.addWidget(self.scan_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

    def set_scanning(self, scanning: bool, message: str = "") -> None:
        self.scan_button.setEnabled(not scanning)
        self.scan_button.setText("Scanning..." if scanning else "Start Scan")
        if scanning:
            self.progress.setRange(0, 0)
            self.status_label.setText(message or "Scanning approved folders...")
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            if message:
                self.status_label.setText(message)

    def update_progress(self, path: str, current: int, total: int) -> None:
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(current)
        self.status_label.setText(f"Scanning {path}")

    def update_summary(self, result: ScanResult | None) -> None:
        if result is None:
            return
        self.recoverable_card.set_value(format_bytes(result.total_recoverable_bytes), f"{len(result.findings)} findings")
        self.unused_card.set_value(str(result.unused_count), "Leftover or unused app data")
        self.cache_card.set_value(str(result.cache_count), "Cache folders identified")
        self.risk_card.set_value(result.risk_label, f"{result.review_count} review, {result.sensitive_count} sensitive")
        self.status_label.setText(
            f"Scan complete. {len(result.findings)} findings, {format_bytes(result.total_recoverable_bytes)} recoverable."
        )
