"""Central colour and typography themes for the Qt widget interface."""

# ruff: noqa: E501

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from bluebubbles.client.ui.models import ThemeName

_THEMES: dict[ThemeName, str] = {
    ThemeName.LIGHT: """
        QWidget { background: #dceafb; color: #172033; font-size: 10pt; }
        QFrame#navigation_header { background: #cfe2f8; border: 1px solid #5798bd; }
        QLabel#application_brand, QLabel[heading="true"] { font-weight: 700; }
        QPushButton#exit_button { background: #ffe1e1; border-color: #c87a7a; }
        QPushButton#help_button, QPushButton#navigation_menu_button {
            background: #b9dff0; border-color: #5798bd; font-weight: 600;
        }
        QFrame#conversation_panel { background: #bfe2f3; border: 1px solid #5798bd; }
        QWidget#chat_workspace { background: #b7cef2; }
        QListWidget#message_list { background: #b7cef2; border: 1px solid #6b819e; }
        QListWidget#conversation_list { background: #f8fbff; border: 1px solid #6b819e; }
        QListWidget#conversation_list::item { padding: 8px; border-bottom: 1px solid #aeb8c7; }
        QListWidget#conversation_list::item:selected { background: #a9d9ef; color: #172033; }
        QLineEdit, QTextEdit, QListWidget, QComboBox, QDoubleSpinBox {
            background: white; border: 1px solid #6b819e; border-radius: 2px; padding: 6px;
        }
        QPushButton { background: #dce9f5; border: 1px solid #6b819e; border-radius: 2px; padding: 6px 10px; }
        QPushButton#primary_button, QPushButton[primary="true"] { background: #1769e0; color: white; border-color: #1769e0; }
        QPushButton#destructive_button { background: #b42318; color: white; border-color: #b42318; }
        QPushButton#message_attachment_button { font-size: 16pt; font-weight: 700; min-width: 28px; }
        QLabel#connection_banner { background: #fff3cd; color: #5f4700; padding: 7px; }
        QLabel#error_banner { background: #fde7e7; color: #7a1712; padding: 7px; }
        QFrame#message_own { background: #d9eaff; border-radius: 8px; }
        QFrame#message_other { background: white; border: 1px solid #d4dae3; border-radius: 8px; }
    """,
    ThemeName.DARK: """
        QWidget { background: #151a22; color: #edf2f7; font-size: 10pt; }
        QFrame#navigation_header { background: #0b1017; border: 1px solid #66758a; }
        QFrame#conversation_panel { background: #182434; border: 1px solid #66758a; }
        QWidget#chat_workspace, QListWidget#message_list { background: #1b2b43; }
        QLabel#application_brand, QLabel[heading="true"] { font-weight: 700; }
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
        QFrame#navigation_header, QFrame#conversation_panel { background: black; border: 2px solid white; }
        QWidget#chat_workspace, QListWidget#message_list { background: black; }
        QLabel#application_brand, QLabel[heading="true"] { font-weight: 700; }
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
