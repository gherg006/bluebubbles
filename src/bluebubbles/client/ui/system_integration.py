"""System tray and privacy-aware desktop notification presentation."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget


class DesktopNotificationManager:
    """Display bounded notification content according to preview policy."""

    def __init__(self, tray: QSystemTrayIcon) -> None:
        self._tray = tray
        self.enabled = True
        self.paused = False
        self.show_previews = False

    def show_message(self, sender: str, preview: str) -> None:
        """Show an accessible privacy-safe new-message notification."""
        if not self.enabled or self.paused:
            return
        title = sender if self.show_previews else "BlueBubbles"
        body = preview if self.show_previews else "New message received."
        self._tray.showMessage(title, body, QSystemTrayIcon.MessageIcon.Information)


class SystemTrayManager:
    """Own tray actions without taking session or business-service ownership."""

    def __init__(
        self,
        application: QApplication,
        window: QWidget,
        *,
        logout: Callable[[], None],
    ) -> None:
        self.tray = QSystemTrayIcon(QIcon(), window)
        self.tray.setToolTip("BlueBubbles — Starting")
        menu = QMenu(window)
        open_action = QAction("Open BlueBubbles", menu)
        open_action.triggered.connect(window.show)
        self.connection_action = QAction("Connection: Starting", menu)
        self.connection_action.setEnabled(False)
        self.unread_action = QAction("Unread: 0", menu)
        self.unread_action.setEnabled(False)
        self.pause_action = QAction("Pause notifications", menu)
        self.pause_action.setCheckable(True)
        logout_action = QAction("Log out", menu)
        logout_action.triggered.connect(logout)
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(application.quit)
        for action in (
            open_action,
            self.connection_action,
            self.unread_action,
            self.pause_action,
            logout_action,
            exit_action,
        ):
            menu.addAction(action)
        self.tray.setContextMenu(menu)
        self.notifications = DesktopNotificationManager(self.tray)
        self.pause_action.toggled.connect(self._set_paused)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def update_connection(self, label: str) -> None:
        """Update tray text with a non-colour connection state."""
        readable = label.replace("_", " ").title()
        self.connection_action.setText(f"Connection: {readable}")
        self.tray.setToolTip(f"BlueBubbles — {readable}")

    def update_unread(self, count: int) -> None:
        """Update the bounded unread summary."""
        self.unread_action.setText(f"Unread: {max(0, count)}")

    def _set_paused(self, paused: bool) -> None:
        self.notifications.paused = paused
