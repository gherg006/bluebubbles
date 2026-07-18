"""Central colour and typography themes for the Qt widget interface."""

# ruff: noqa: E501

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from bluebubbles.client.ui.models import ThemeName

_THEMES: dict[ThemeName, str] = {
    ThemeName.LIGHT: """
        QWidget { background: #f6f7f9; color: #172033; font-size: 10pt; }
        QFrame#navigation_sidebar { background: #183153; }
        QFrame#navigation_sidebar QPushButton { color: white; border: 0; padding: 9px; }
        QFrame#navigation_sidebar QPushButton:checked { background: #2f6feb; }
        QLineEdit, QTextEdit, QListWidget, QComboBox, QDoubleSpinBox {
            background: white; border: 1px solid #aeb8c7; border-radius: 5px; padding: 6px;
        }
        QPushButton { background: #e5e9f0; border: 1px solid #aeb8c7; border-radius: 5px; padding: 6px 10px; }
        QPushButton#primary_button, QPushButton[primary="true"] { background: #1769e0; color: white; border-color: #1769e0; }
        QPushButton#destructive_button { background: #b42318; color: white; border-color: #b42318; }
        QLabel#connection_banner { background: #fff3cd; color: #5f4700; padding: 7px; }
        QLabel#error_banner { background: #fde7e7; color: #7a1712; padding: 7px; }
        QFrame#message_own { background: #d9eaff; border-radius: 8px; }
        QFrame#message_other { background: white; border: 1px solid #d4dae3; border-radius: 8px; }
    """,
    ThemeName.DARK: """
        QWidget { background: #151a22; color: #edf2f7; font-size: 10pt; }
        QFrame#navigation_sidebar { background: #0b1017; }
        QFrame#navigation_sidebar QPushButton { color: #edf2f7; border: 0; padding: 9px; }
        QFrame#navigation_sidebar QPushButton:checked { background: #315cba; }
        QLineEdit, QTextEdit, QListWidget, QComboBox, QDoubleSpinBox {
            background: #202834; border: 1px solid #66758a; border-radius: 5px; padding: 6px;
        }
        QPushButton { background: #293342; border: 1px solid #66758a; border-radius: 5px; padding: 6px 10px; }
        QPushButton#primary_button, QPushButton[primary="true"] { background: #4c82ee; color: white; }
        QPushButton#destructive_button { background: #d33b32; color: white; }
        QLabel#connection_banner { background: #594600; color: #fff2b3; padding: 7px; }
        QLabel#error_banner { background: #5b201d; color: #ffd8d4; padding: 7px; }
        QFrame#message_own { background: #244a78; border-radius: 8px; }
        QFrame#message_other { background: #202834; border: 1px solid #66758a; border-radius: 8px; }
    """,
    ThemeName.HIGH_CONTRAST: """
        QWidget { background: black; color: white; font-size: 11pt; }
        QFrame#navigation_sidebar { background: black; border-right: 2px solid white; }
        QFrame#navigation_sidebar QPushButton { color: white; border: 2px solid white; padding: 8px; }
        QFrame#navigation_sidebar QPushButton:checked { background: #ffff00; color: black; }
        QLineEdit, QTextEdit, QListWidget, QComboBox, QDoubleSpinBox {
            background: black; color: white; border: 2px solid white; padding: 6px;
        }
        QPushButton { background: black; color: white; border: 2px solid white; padding: 6px 10px; }
        QPushButton#primary_button, QPushButton[primary="true"] { background: #ffff00; color: black; }
        QPushButton#destructive_button { background: black; color: #ffff00; border-color: #ffff00; }
        QLabel#connection_banner, QLabel#error_banner { background: #ffff00; color: black; padding: 7px; }
        QFrame#message_own, QFrame#message_other { background: black; border: 2px solid white; }
    """,
}


class ThemeManager:
    """Apply a named stylesheet and scalable application font."""

    def __init__(self, application: QApplication) -> None:
        self._application = application
        current = application.font().pointSizeF()
        self._base_font_size = current if current > 0 else 10.0

    def apply(self, theme: ThemeName, font_scale: float = 1.0) -> None:
        """Apply the selected theme and bounded device-independent font scale."""
        if not 0.75 <= font_scale <= 2.0:
            raise ValueError("Font scale must be between 75% and 200%.")
        self._application.setStyleSheet(_THEMES[theme])
        font = self._application.font()
        font.setPointSizeF(self._base_font_size * font_scale)
        self._application.setFont(font)
