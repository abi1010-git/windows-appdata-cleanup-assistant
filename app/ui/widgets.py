from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from app.models import RISK_REVIEW, RISK_SAFE, RISK_SENSITIVE


def icon(style: QStyle, name: QStyle.StandardPixmap):
    return style.standardIcon(name)


def make_tool_button(parent: QWidget, pixmap: QStyle.StandardPixmap, tooltip: str) -> QPushButton:
    button = QPushButton(parent)
    button.setIcon(parent.style().standardIcon(pixmap))
    button.setIconSize(QSize(18, 18))
    button.setFixedSize(38, 34)
    button.setToolTip(tooltip)
    return button


def add_shadow(frame: QFrame, blur: int = 28, alpha: int = 70) -> None:
    shadow = QGraphicsDropShadowEffect(frame)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, 8)
    shadow.setColor(QColor(0, 0, 0, alpha))
    frame.setGraphicsEffect(shadow)


class SummaryCard(QFrame):
    def __init__(self, title: str, value: str = "-", caption: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setMinimumHeight(118)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        add_shadow(self, blur=18, alpha=40)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("Muted")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("Metric")
        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("Muted")
        self.caption_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch(1)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str, caption: str | None = None) -> None:
        self.value_label.setText(value)
        if caption is not None:
            self.caption_label.setText(caption)


class RiskBadge(QLabel):
    COLORS = {
        RISK_SAFE: ("#103d2c", "#46d17d", "Safe"),
        RISK_REVIEW: ("#473817", "#f0c255", "Review"),
        RISK_SENSITIVE: ("#4b202b", "#ff7a90", "Sensitive"),
    }

    def __init__(self, risk: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(74)
        self.setFixedHeight(24)
        self.set_risk(risk)

    def set_risk(self, risk: str) -> None:
        bg, fg, text = self.COLORS.get(risk, ("#313744", "#d0d7e2", risk.title()))
        self.setText(text)
        self.setStyleSheet(
            f"border-radius: 12px; padding: 3px 8px; background: {bg}; color: {fg}; font-weight: 700;"
        )


class EmptyState(QFrame):
    def __init__(self, title: str, message: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Panel")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(24, 24, 24, 24)
        title_label = QLabel(title)
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label = QLabel(message)
        message_label.setObjectName("Muted")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(message_label)


def page_header(title: str, subtitle: str) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title_label = QLabel(title)
    title_label.setObjectName("Title")
    subtitle_label = QLabel(subtitle)
    subtitle_label.setObjectName("Muted")
    subtitle_label.setWordWrap(True)
    layout.addWidget(title_label)
    layout.addWidget(subtitle_label)
    return container


def horizontal_cards(cards: list[SummaryCard]) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(14)
    for card in cards:
        layout.addWidget(card)
    return widget
