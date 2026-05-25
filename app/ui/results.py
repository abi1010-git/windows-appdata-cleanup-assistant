from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QAbstractItemView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models import Finding, STATUS_CLEANED, STATUS_IGNORED
from app.ui.widgets import EmptyState, RiskBadge, page_header


class NumericTableItem(QTableWidgetItem):
    def __lt__(self, other: QTableWidgetItem) -> bool:
        return int(self.data(Qt.ItemDataRole.UserRole) or 0) < int(other.data(Qt.ItemDataRole.UserRole) or 0)


class ResultsPage(QWidget):
    cleanup_requested = pyqtSignal(object)
    ignore_requested = pyqtSignal(object)
    open_requested = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.findings: list[Finding] = []
        self.filtered: list[Finding] = []
        self.selected_finding: Finding | None = None
        self.search_text = ""

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Folder", "Size", "Last Used", "Risk", "Status", "Category", "Action"])
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._selection_changed)

        self.detail_panel = self._build_detail_panel()
        self.empty_state = EmptyState("No scan results yet", "Run a scan from the dashboard to review cleanup candidates.")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.table)
        splitter.addWidget(self.detail_panel)
        splitter.setSizes([780, 340])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(page_header("Scan Results", "Review each finding before moving anything to the Recycle Bin."))
        layout.addWidget(splitter, stretch=1)
        layout.addWidget(self.empty_state)
        self._update_empty_state()

    def _build_detail_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.detail_title = QLabel("Folder Details")
        self.detail_title.setObjectName("Title")
        self.path_label = QLabel("Select a result")
        self.path_label.setWordWrap(True)
        self.path_label.setObjectName("Muted")
        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)
        self.meta_label.setObjectName("Muted")
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMinimumHeight(180)

        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(lambda: self._emit_for_selected(self.open_requested))
        self.cleanup_button = QPushButton("Move To Recycle Bin")
        self.cleanup_button.setObjectName("Danger")
        self.cleanup_button.clicked.connect(lambda: self._emit_for_selected(self.cleanup_requested))
        self.ignore_button = QPushButton("Ignore")
        self.ignore_button.clicked.connect(lambda: self._emit_for_selected(self.ignore_requested))

        actions = QHBoxLayout()
        actions.setSpacing(8)
        actions.addWidget(self.open_button)
        actions.addWidget(self.cleanup_button)
        actions.addWidget(self.ignore_button)

        layout.addWidget(self.detail_title)
        layout.addWidget(self.path_label)
        layout.addWidget(self.meta_label)
        layout.addWidget(self.analysis_text)
        layout.addLayout(actions)
        layout.addStretch(1)
        return panel

    def set_findings(self, findings: list[Finding]) -> None:
        self.findings = findings
        self.apply_search(self.search_text)

    def apply_search(self, text: str) -> None:
        self.search_text = text.casefold().strip()
        if not self.search_text:
            self.filtered = list(self.findings)
        else:
            self.filtered = [
                finding
                for finding in self.findings
                if self.search_text in finding.path.casefold()
                or self.search_text in (finding.detected_app or "").casefold()
                or self.search_text in finding.category.casefold()
            ]
        self._populate_table()

    def _populate_table(self) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for row, finding in enumerate(self.filtered):
            self.table.insertRow(row)
            name_item = QTableWidgetItem(finding.name)
            name_item.setData(Qt.ItemDataRole.UserRole, row)
            name_item.setToolTip(finding.path)
            self.table.setItem(row, 0, name_item)

            size_item = NumericTableItem(finding.size_label)
            size_item.setData(Qt.ItemDataRole.UserRole, finding.size_bytes)
            self.table.setItem(row, 1, size_item)
            last_used_item = QTableWidgetItem(finding.last_used_label)
            last_used_item.setData(Qt.ItemDataRole.UserRole, row)
            self.table.setItem(row, 2, last_used_item)
            self.table.setCellWidget(row, 3, RiskBadge(finding.risk))
            status_item = QTableWidgetItem(finding.status.title())
            status_item.setData(Qt.ItemDataRole.UserRole, row)
            self.table.setItem(row, 4, status_item)
            category_item = QTableWidgetItem(finding.category.replace("_", " ").title())
            category_item.setData(Qt.ItemDataRole.UserRole, row)
            self.table.setItem(row, 5, category_item)
            action_item = QTableWidgetItem("Eligible" if finding.cleanup_eligible else "Review")
            action_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            action_item.setData(Qt.ItemDataRole.UserRole, row)
            self.table.setItem(row, 6, action_item)
        self.table.setSortingEnabled(True)
        self._update_empty_state()
        if self.filtered:
            self.table.selectRow(0)
        else:
            self._show_detail(None)

    def _selection_changed(self) -> None:
        items = self.table.selectedItems()
        if not items:
            self._show_detail(None)
            return
        row = self.table.currentRow()
        source_row = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 and self.table.item(row, 0) else None
        if source_row is None:
            source_row = items[0].data(Qt.ItemDataRole.UserRole)
        try:
            finding = self.filtered[int(source_row)]
        except (IndexError, TypeError, ValueError):
            finding = None
        self._show_detail(finding)

    def _show_detail(self, finding: Finding | None) -> None:
        self.selected_finding = finding
        if finding is None:
            self.path_label.setText("Select a result")
            self.meta_label.setText("")
            self.analysis_text.setPlainText("")
            self.open_button.setEnabled(False)
            self.cleanup_button.setEnabled(False)
            self.ignore_button.setEnabled(False)
            return
        self.path_label.setText(finding.path)
        app = finding.detected_app or "Unknown"
        installed = "installed" if finding.is_installed else "not found" if finding.is_installed is False else "unknown"
        self.meta_label.setText(
            f"Size: {finding.size_label}\nLast modified: {finding.last_used_label}\nDetected app: {app} ({installed})"
        )
        self.analysis_text.setPlainText(f"{finding.explanation}\n\nRecommendation: {finding.recommendation}")
        path_exists = Path(finding.path).exists()
        self.open_button.setEnabled(path_exists)
        self.cleanup_button.setEnabled(finding.cleanup_eligible and finding.status not in {STATUS_CLEANED, STATUS_IGNORED})
        self.ignore_button.setEnabled(finding.status not in {STATUS_CLEANED, STATUS_IGNORED})

    def _emit_for_selected(self, signal) -> None:
        if self.selected_finding is not None:
            signal.emit(self.selected_finding)

    def refresh_selected(self) -> None:
        self._populate_table()

    def _update_empty_state(self) -> None:
        has_results = bool(self.filtered)
        self.table.setVisible(has_results)
        self.detail_panel.setVisible(has_results)
        self.empty_state.setVisible(not has_results)

    @staticmethod
    def open_path(finding: Finding) -> None:
        path = str(Path(finding.path))
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
