from __future__ import annotations

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.models import format_bytes
from app.ui.widgets import EmptyState, page_header


class HistoryPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Completed", "Findings", "Recoverable", "Errors"])
        self.table.verticalHeader().setVisible(False)
        self.empty = EmptyState("No scan history yet", "Completed scans will appear here.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(page_header("Scan History", "Track scan results and cleanup opportunities over time."))
        layout.addWidget(self.table, stretch=1)
        layout.addWidget(self.empty)
        self.update_history([])

    def update_history(self, rows: list[dict]) -> None:
        self.table.setRowCount(0)
        self.empty.setVisible(not rows)
        self.table.setVisible(bool(rows))
        for row_index, row in enumerate(rows):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(row.get("completed_at", ""))))
            self.table.setItem(row_index, 1, QTableWidgetItem(str(row.get("finding_count", 0))))
            self.table.setItem(row_index, 2, QTableWidgetItem(format_bytes(int(row.get("recoverable_bytes", 0)))))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(row.get("errors_json", "[]"))))
