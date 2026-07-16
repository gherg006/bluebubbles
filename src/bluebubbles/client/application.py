"""Application factory and minimal window for the BlueBubbles desktop client."""

from collections.abc import Sequence
from typing import cast

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from bluebubbles.version import __version__


class ClientApplication:
    """Own the Qt application and its minimal foundation-stage main window."""

    def __init__(self, arguments: Sequence[str]) -> None:
        """Initialise Qt metadata and construct the initial main window."""
        existing_application = QApplication.instance()
        if existing_application is None:
            self.qt_application = QApplication(list(arguments))
        else:
            self.qt_application = cast(QApplication, existing_application)
        self.qt_application.setApplicationName("BlueBubbles")
        self.qt_application.setApplicationVersion(__version__)

        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("BlueBubbles")
        self.main_window.setCentralWidget(
            QLabel("BlueBubbles client foundation is ready.")
        )
        self.main_window.resize(640, 400)

    def run(self) -> int:
        """Show the main window and return the Qt event-loop exit status."""
        self.main_window.show()
        return self.qt_application.exec()


def create_application(arguments: Sequence[str]) -> ClientApplication:
    """Create an independently testable desktop application instance."""
    return ClientApplication(arguments)
