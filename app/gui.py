from __future__ import annotations

import copy
import os
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.cleanup import CleanupError, CleanupManager
from app.config import APP_NAME, AppSettings
from app.database import StorageDatabase
from app.models import Finding, ScanResult
from app.scanner import ScannerConfig, StorageScanner
from app.styles.theme import apply_theme
from app.ui.analytics import AnalyticsPage
from app.ui.dashboard import DashboardPage
from app.ui.history import HistoryPage
from app.ui.results import ResultsPage
from app.ui.settings import SettingsPage
from app.ui.widgets import make_tool_button


class ScanWorker(QObject):
    progress = pyqtSignal(str, int, int)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, config: ScannerConfig) -> None:
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            scanner = StorageScanner(self.config)
            result = scanner.scan(progress=lambda path, current, total: self.progress.emit(path, current, total))
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


class MainWindow(QMainWindow):
    def __init__(self, database: StorageDatabase | None = None) -> None:
        super().__init__()
        self.database = database or StorageDatabase()
        self.settings = self.database.load_settings()
        ignored_paths = self.database.ignored_paths()
        self.settings.excluded_paths = sorted(set(self.settings.excluded_paths + ignored_paths))
        self.scan_thread: QThread | None = None
        self.scan_worker: ScanWorker | None = None
        self.current_result: ScanResult | None = None

        self.setWindowTitle(APP_NAME)
        self.resize(1240, 820)
        self.setMinimumSize(980, 640)
        self._build_shell()
        self._wire_signals()
        self._load_initial_state()

    def _build_shell(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search folders, apps, or categories")
        self.scan_status_label = QLabel("Ready")
        self.scan_status_label.setObjectName("Muted")

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(18, 12, 18, 12)
        logo = QLabel("Storage Detective")
        logo.setObjectName("Title")
        self.theme_button = make_tool_button(self, QStyle.StandardPixmap.SP_DialogResetButton, "Toggle theme")
        self.settings_button = make_tool_button(self, QStyle.StandardPixmap.SP_FileDialogDetailedView, "Settings")
        top_layout.addWidget(logo)
        top_layout.addSpacing(18)
        top_layout.addWidget(self.search_input, stretch=1)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.scan_status_label)
        top_layout.addWidget(self.theme_button)
        top_layout.addWidget(self.settings_button)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 18, 12, 18)
        side_layout.setSpacing(8)

        self.nav_buttons: list[QPushButton] = []
        nav_items = [
            ("Dashboard", QStyle.StandardPixmap.SP_ComputerIcon),
            ("Scan Results", QStyle.StandardPixmap.SP_DirIcon),
            ("Analytics", QStyle.StandardPixmap.SP_FileDialogInfoView),
            ("Settings", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("Scan History", QStyle.StandardPixmap.SP_BrowserReload),
        ]
        for index, (label, icon_id) in enumerate(nav_items):
            button = QPushButton(label)
            button.setObjectName("SidebarButton")
            button.setCheckable(True)
            button.setIcon(self.style().standardIcon(icon_id))
            button.clicked.connect(lambda checked=False, i=index: self._set_page(i))
            side_layout.addWidget(button)
            self.nav_buttons.append(button)
        side_layout.addStretch(1)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.results_page = ResultsPage()
        self.analytics_page = AnalyticsPage()
        self.settings_page = SettingsPage()
        self.history_page = HistoryPage()
        for page in [
            self.dashboard_page,
            self.results_page,
            self.analytics_page,
            self.settings_page,
            self.history_page,
        ]:
            self.stack.addWidget(page)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.stack, stretch=1)

        root_layout.addWidget(top_bar)
        root_layout.addWidget(body, stretch=1)
        self.setCentralWidget(root)
        self._set_page(0)

    def _wire_signals(self) -> None:
        self.dashboard_page.scan_requested.connect(self.start_scan)
        self.results_page.cleanup_requested.connect(self.cleanup_finding)
        self.results_page.ignore_requested.connect(self.ignore_finding)
        self.results_page.open_requested.connect(self.open_finding)
        self.settings_page.settings_saved.connect(self.save_settings)
        self.search_input.textChanged.connect(self.results_page.apply_search)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.settings_button.clicked.connect(lambda: self._set_page(3))

    def _load_initial_state(self) -> None:
        self.settings_page.set_settings(self.settings)
        recent = self.database.recent_findings()
        if recent:
            self.results_page.set_findings(recent)
        self.history_page.update_history(self.database.scan_history())

    def _set_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

    def start_scan(self) -> None:
        if self.scan_thread is not None:
            return
        self.scan_status_label.setText("Scanning")
        self.dashboard_page.set_scanning(True)
        settings = copy.deepcopy(self.settings)
        settings.excluded_paths = sorted(set(settings.excluded_paths + self.database.ignored_paths()))
        config = ScannerConfig.from_settings(settings)
        self.scan_thread = QThread(self)
        self.scan_worker = ScanWorker(config)
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.progress.connect(self.dashboard_page.update_progress)
        self.scan_worker.finished.connect(self._scan_finished)
        self.scan_worker.failed.connect(self._scan_failed)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.failed.connect(self.scan_thread.quit)
        self.scan_thread.finished.connect(self._scan_thread_finished)
        self.scan_thread.start()

    def _scan_finished(self, result: ScanResult) -> None:
        self.current_result = result
        self.database.save_scan(result)
        self.dashboard_page.set_scanning(False)
        self.dashboard_page.update_summary(result)
        self.results_page.set_findings(result.findings)
        self.analytics_page.update_result(result)
        self.history_page.update_history(self.database.scan_history())
        self.scan_status_label.setText("Scan complete")
        self._set_page(1)

    def _scan_failed(self, message: str) -> None:
        self.dashboard_page.set_scanning(False, "Scan failed.")
        self.scan_status_label.setText("Scan failed")
        QMessageBox.warning(self, "Scan failed", message)

    def _scan_thread_finished(self) -> None:
        if self.scan_worker is not None:
            self.scan_worker.deleteLater()
        if self.scan_thread is not None:
            self.scan_thread.deleteLater()
        self.scan_thread = None
        self.scan_worker = None

    def cleanup_finding(self, finding: Finding) -> None:
        answer = QMessageBox.question(
            self,
            "Move to Recycle Bin?",
            f"Move this folder to the Recycle Bin?\n\n{finding.path}\n\nNo files will be permanently deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        manager = CleanupManager(ScannerConfig.from_settings(self.settings).scan_roots, self.settings.excluded_paths)
        try:
            manager.move_to_recycle_bin(finding, confirmed=True)
        except CleanupError as exc:
            QMessageBox.warning(self, "Cleanup blocked", str(exc))
            return
        self.database.record_cleanup(finding)
        self.results_page.refresh_selected()
        self.history_page.update_history(self.database.scan_history())
        self.scan_status_label.setText("Moved to Recycle Bin")

    def ignore_finding(self, finding: Finding) -> None:
        self.database.mark_ignored(finding)
        if finding.path not in self.settings.excluded_paths:
            self.settings.excluded_paths.append(finding.path)
            self.database.save_settings(self.settings)
            self.settings_page.set_settings(self.settings)
        self.results_page.refresh_selected()
        self.scan_status_label.setText("Ignored")

    def open_finding(self, finding: Finding) -> None:
        path = Path(finding.path)
        if not path.exists():
            QMessageBox.information(self, "Folder unavailable", "This folder no longer exists.")
            return
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]

    def save_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.database.save_settings(settings)
        apply_theme(QApplication.instance(), settings.theme)
        self.scan_status_label.setText("Settings saved")

    def toggle_theme(self) -> None:
        self.settings.theme = "light" if self.settings.theme == "dark" else "dark"
        self.database.save_settings(self.settings)
        self.settings_page.set_settings(self.settings)
        apply_theme(QApplication.instance(), self.settings.theme)


def create_window(database: StorageDatabase | None = None) -> MainWindow:
    return MainWindow(database=database)
