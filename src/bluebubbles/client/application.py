"""Application factory and minimal window for the BlueBubbles desktop client."""

from collections.abc import Sequence
from typing import cast
from uuid import UUID

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from bluebubbles.client.bootstrap import (
    build_authenticated_container,
    build_unauthenticated_container,
    verify_client_environment,
)
from bluebubbles.client.configuration.loader import ClientConfigurationLoader
from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.client.container import ClientContainer
from bluebubbles.client.security.secure_store import SecureStore
from bluebubbles.version import __version__


class ClientApplication:
    """Own the Qt application and its minimal foundation-stage main window."""

    def __init__(
        self, arguments: Sequence[str], settings: ClientSettings | None = None
    ) -> None:
        """Initialise Qt metadata and construct the initial main window."""
        self.settings = settings or ClientConfigurationLoader().load_client_settings()
        verify_client_environment(self.settings)
        self.container: ClientContainer = build_unauthenticated_container(self.settings)
        self.authenticated_container: ClientContainer | None = None
        existing_application = QApplication.instance()
        if existing_application is None:
            self.qt_application = QApplication(list(arguments))
        else:
            self.qt_application = cast(QApplication, existing_application)
        self.qt_application.setApplicationName(self.settings.application.name)
        self.qt_application.setApplicationVersion(__version__)

        self.main_window = QMainWindow()
        self.main_window.setWindowTitle(self.settings.application.name)
        self.main_window.setCentralWidget(
            QLabel(f"Configured for {self.settings.server.base_url.host}")
        )
        self.main_window.resize(640, 400)

    def run(self) -> int:
        """Show the main window and return the Qt event-loop exit status."""
        self.main_window.show()
        try:
            return self.qt_application.exec()
        finally:
            self.container.close()

    async def activate_authenticated_profile(
        self, profile_id: UUID, secure_store: SecureStore
    ) -> ClientContainer:
        """Open and own one disposable authenticated local-storage container."""
        if self.authenticated_container is not None:
            await self.authenticated_container.stop()
        container = build_authenticated_container(
            self.settings, profile_id, secure_store
        )
        await container.start()
        self.authenticated_container = container
        return container

    async def logout(self) -> None:
        """Close authenticated local storage and clear its in-memory keys."""
        if self.authenticated_container is not None:
            await self.authenticated_container.stop()
            self.authenticated_container = None


def create_application(
    arguments: Sequence[str], settings: ClientSettings | None = None
) -> ClientApplication:
    """Create an independently testable desktop application instance."""
    return ClientApplication(arguments, settings)
