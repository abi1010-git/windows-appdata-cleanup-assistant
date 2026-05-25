from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication


DARK_QSS = """
QWidget {
    background: #111318;
    color: #eef1f7;
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    font-size: 13px;
}
QMainWindow, QStackedWidget {
    background: #111318;
}
QFrame#TopBar {
    background: #171a21;
    border-bottom: 1px solid #272c36;
}
QFrame#Sidebar {
    background: #151820;
    border-right: 1px solid #272c36;
}
QFrame#Card, QFrame#Panel {
    background: #1b2029;
    border: 1px solid #2b313d;
    border-radius: 8px;
}
QLabel#Muted {
    color: #97a0b2;
}
QLabel#Title {
    font-size: 22px;
    font-weight: 700;
}
QLabel#Metric {
    font-size: 24px;
    font-weight: 700;
}
QPushButton {
    background: #252b36;
    border: 1px solid #333a48;
    border-radius: 7px;
    padding: 8px 12px;
    color: #f4f7fb;
}
QPushButton:hover {
    background: #2e3542;
}
QPushButton:pressed {
    background: #384151;
}
QPushButton#Primary {
    background: #3d7bfd;
    border-color: #4f8aff;
    color: white;
    font-weight: 600;
}
QPushButton#Primary:hover {
    background: #4a86ff;
}
QPushButton#Danger {
    background: #433039;
    border-color: #734558;
    color: #ffd7df;
}
QPushButton#SidebarButton {
    background: transparent;
    border: 0;
    border-radius: 8px;
    text-align: left;
    padding: 10px 12px;
    color: #c8cfdd;
}
QPushButton#SidebarButton:hover {
    background: #202631;
}
QPushButton#SidebarButton:checked {
    background: #263249;
    color: #ffffff;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #151922;
    border: 1px solid #303746;
    border-radius: 7px;
    padding: 7px 9px;
    selection-background-color: #3d7bfd;
}
QTableWidget {
    background: #151922;
    alternate-background-color: #181d26;
    border: 1px solid #2b313d;
    border-radius: 8px;
    gridline-color: #27303d;
}
QHeaderView::section {
    background: #1f2530;
    border: 0;
    border-right: 1px solid #2c3441;
    padding: 8px;
    color: #bfc7d5;
    font-weight: 600;
}
QTableWidget::item {
    padding: 8px;
}
QTableWidget::item:selected {
    background: #2a3f68;
}
QProgressBar {
    background: #171b23;
    border: 1px solid #2c3441;
    border-radius: 7px;
    height: 12px;
    text-align: center;
}
QProgressBar::chunk {
    background: #3d7bfd;
    border-radius: 6px;
}
QScrollBar:vertical {
    background: #151922;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #303746;
    border-radius: 6px;
}
QCheckBox {
    spacing: 8px;
}
"""


LIGHT_QSS = """
QWidget {
    background: #f6f7fb;
    color: #1f2530;
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    font-size: 13px;
}
QFrame#TopBar, QFrame#Sidebar, QFrame#Card, QFrame#Panel {
    background: #ffffff;
    border: 1px solid #dde2ec;
    border-radius: 8px;
}
QFrame#TopBar {
    border-radius: 0;
    border-left: 0;
    border-right: 0;
    border-top: 0;
}
QFrame#Sidebar {
    border-radius: 0;
    border-left: 0;
    border-top: 0;
    border-bottom: 0;
}
QLabel#Muted {
    color: #667085;
}
QLabel#Title {
    font-size: 22px;
    font-weight: 700;
}
QLabel#Metric {
    font-size: 24px;
    font-weight: 700;
}
QPushButton {
    background: #eef2f8;
    border: 1px solid #d4dbe8;
    border-radius: 7px;
    padding: 8px 12px;
}
QPushButton:hover {
    background: #e5ebf5;
}
QPushButton#Primary {
    background: #2f6df6;
    border-color: #2f6df6;
    color: white;
    font-weight: 600;
}
QPushButton#Danger {
    background: #fff1f3;
    border-color: #ffd0d9;
    color: #a6243d;
}
QPushButton#SidebarButton {
    background: transparent;
    border: 0;
    text-align: left;
    padding: 10px 12px;
    color: #344054;
}
QPushButton#SidebarButton:hover {
    background: #eef2f8;
}
QPushButton#SidebarButton:checked {
    background: #dfe9ff;
    color: #153f9d;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #ffffff;
    border: 1px solid #d4dbe8;
    border-radius: 7px;
    padding: 7px 9px;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #dde2ec;
    border-radius: 8px;
    gridline-color: #e5eaf2;
}
QHeaderView::section {
    background: #eef2f8;
    border: 0;
    border-right: 1px solid #dde2ec;
    padding: 8px;
    color: #475467;
    font-weight: 600;
}
QProgressBar {
    background: #eef2f8;
    border: 1px solid #d4dbe8;
    border-radius: 7px;
    height: 12px;
}
QProgressBar::chunk {
    background: #2f6df6;
    border-radius: 6px;
}
"""


def apply_theme(app: QApplication, theme: str = "dark") -> None:
    app.setFont(QFont("Segoe UI", 10))
    try:
        import qdarktheme

        qdarktheme.setup_theme("dark" if theme == "dark" else "light")
    except Exception:
        pass
    app.setStyleSheet(DARK_QSS if theme == "dark" else LIGHT_QSS)

