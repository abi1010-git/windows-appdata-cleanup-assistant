from __future__ import annotations

from collections import Counter

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.models import ScanResult, format_bytes
from app.ui.widgets import EmptyState, page_header


class AnalyticsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.result: ScanResult | None = None
        self.content = QVBoxLayout()
        self.content.setSpacing(10)
        self.empty = EmptyState("No analytics yet", "Run a scan to see storage breakdowns and cleanup trends.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(page_header("Analytics", "Storage usage by category, largest folders, and cleanup history."))
        layout.addLayout(self.content)
        layout.addWidget(self.empty)
        layout.addStretch(1)

    def update_result(self, result: ScanResult | None) -> None:
        self.result = result
        self._clear_content()
        if not result or not result.findings:
            self.empty.setVisible(True)
            return
        self.empty.setVisible(False)
        try:
            self._add_matplotlib_charts(result)
        except Exception:
            self._add_text_fallback(result)

    def _add_matplotlib_charts(self, result: ScanResult) -> None:
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure

        category_sizes = Counter()
        for finding in result.findings:
            category_sizes[finding.category.replace("_", " ").title()] += finding.size_bytes

        fig = Figure(figsize=(8, 4), dpi=100)
        fig.patch.set_alpha(0)
        axes = fig.subplots(1, 2)
        labels = list(category_sizes.keys())
        values = [category_sizes[label] / (1024**2) for label in labels]
        axes[0].bar(labels, values, color="#3d7bfd")
        axes[0].set_title("Usage by Category")
        axes[0].tick_params(axis="x", rotation=35)
        axes[0].set_ylabel("MB")

        largest = result.findings[:5]
        axes[1].barh([f.name[:20] for f in largest], [f.size_bytes / (1024**2) for f in largest], color="#46d17d")
        axes[1].set_title("Largest Folders")
        axes[1].invert_yaxis()
        for ax in axes:
            ax.grid(True, alpha=0.2)
        fig.tight_layout()
        self.content.addWidget(FigureCanvas(fig))

    def _add_text_fallback(self, result: ScanResult) -> None:
        category_sizes = Counter()
        for finding in result.findings:
            category_sizes[finding.category] += finding.size_bytes
        for category, size in category_sizes.most_common():
            label = QLabel(f"{category.replace('_', ' ').title()}: {format_bytes(size)}")
            label.setObjectName("Muted")
            self.content.addWidget(label)

    def _clear_content(self) -> None:
        while self.content.count():
            item = self.content.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
