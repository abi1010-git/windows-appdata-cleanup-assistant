from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import AppSettings
from app.ui.widgets import page_header


class SettingsPage(QWidget):
    settings_saved = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.excluded_list = QListWidget()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 4)
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 2048)
        self.min_size_spin.setSuffix(" MB")
        self.ai_check = QCheckBox("AI-style explanations")
        self.exclusion_input = QLineEdit()
        self.exclusion_input.setPlaceholderText(r"C:\Users\you\AppData\Local\AppName")
        self.add_exclusion_button = QPushButton("Add")
        self.remove_exclusion_button = QPushButton("Remove Selected")
        self.save_button = QPushButton("Save Settings")
        self.save_button.setObjectName("Primary")
        self.save_button.clicked.connect(self._save)
        self.add_exclusion_button.clicked.connect(self._add_exclusion)
        self.remove_exclusion_button.clicked.connect(self._remove_selected_exclusion)

        panel = QFrame()
        panel.setObjectName("Panel")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 18, 18, 18)
        form.setSpacing(12)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Scan depth", self.depth_spin)
        form.addRow("Minimum folder size", self.min_size_spin)
        form.addRow("Explanations", self.ai_check)

        excluded_panel = QFrame()
        excluded_panel.setObjectName("Panel")
        excluded_layout = QVBoxLayout(excluded_panel)
        excluded_layout.setContentsMargins(18, 18, 18, 18)
        excluded_title = QLabel("Excluded Folders")
        excluded_title.setObjectName("Title")
        excluded_note = QLabel("Ignored folders and manual exclusions are skipped during scans.")
        excluded_note.setObjectName("Muted")
        excluded_note.setWordWrap(True)
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        add_row.addWidget(self.exclusion_input, stretch=1)
        add_row.addWidget(self.add_exclusion_button)
        excluded_layout.addWidget(excluded_title)
        excluded_layout.addWidget(excluded_note)
        excluded_layout.addLayout(add_row)
        excluded_layout.addWidget(self.excluded_list)
        excluded_layout.addWidget(self.remove_exclusion_button)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(page_header("Settings", "Tune scanning behavior while keeping cleanup conservative."))
        layout.addWidget(panel)
        layout.addWidget(excluded_panel, stretch=1)
        layout.addLayout(actions)

    def set_settings(self, settings: AppSettings) -> None:
        self.theme_combo.setCurrentText(settings.theme)
        self.depth_spin.setValue(settings.scan_depth)
        self.min_size_spin.setValue(settings.min_folder_size_mb)
        self.ai_check.setChecked(settings.ai_explanations_enabled)
        self.excluded_list.clear()
        self.excluded_list.addItems(settings.excluded_paths)

    def current_settings(self) -> AppSettings:
        paths = [self.excluded_list.item(i).text() for i in range(self.excluded_list.count())]
        return AppSettings(
            excluded_paths=paths,
            theme=self.theme_combo.currentText(),
            scan_depth=self.depth_spin.value(),
            ai_explanations_enabled=self.ai_check.isChecked(),
            min_folder_size_mb=self.min_size_spin.value(),
        )

    def _save(self) -> None:
        self.settings_saved.emit(self.current_settings())

    def _add_exclusion(self) -> None:
        value = self.exclusion_input.text().strip()
        if not value:
            return
        existing = {self.excluded_list.item(i).text() for i in range(self.excluded_list.count())}
        if value not in existing:
            self.excluded_list.addItem(value)
        self.exclusion_input.clear()

    def _remove_selected_exclusion(self) -> None:
        for item in self.excluded_list.selectedItems():
            row = self.excluded_list.row(item)
            self.excluded_list.takeItem(row)
