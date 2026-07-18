"""Application factory and lifecycle owner for the BlueBubbles desktop client."""

from collections.abc import Sequence
from typing import cast
from uuid import UUID

from PySide6.QtWidgets import QApplication, QMainWindow

from bluebubbles.client.bootstrap import (
    build_authenticated_container,
    build_unauthenticated_container,
    verify_client_environment,
)
from bluebubbles.client.configuration.loader import ClientConfigurationLoader
from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.client.container import ClientContainer
from bluebubbles.client.security.secure_store import SecureStore
from bluebubbles.client.ui.backend import UiBackend, UnavailableUiBackend
from bluebubbles.client.ui.tasks import BackgroundTaskRunner
from bluebubbles.client.ui.viewmodels import DesktopViewModel, LoginViewModel
from bluebubbles.client.ui.windows import LoginWindow, MainWindow
from bluebubbles.version import __version__


class ClientApplication:
    """Own the Qt application and its minimal foundation-stage main window."""

    def __init__(
        self,
        arguments: Sequence[str],
        settings: ClientSettings | None = None,
        backend: UiBackend | None = None,
    ) -> None:
        """Initialise Qt metadata, service ViewModels and the login window."""
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
        self.backend = backend or UnavailableUiBackend()
        self.task_runner = BackgroundTaskRunner()
        self.login_view_model = LoginViewModel(self.backend, self.task_runner)
        self.login_window = LoginWindow(
            self.login_view_model,
            application_name=self.settings.application.name,
            default_server=str(self.settings.server.base_url),
        )
        self.desktop_view_model: DesktopViewModel | None = None
        self.desktop_window: MainWindow | None = None
        self.main_window: QMainWindow = self.login_window
        self.login_view_model.authenticated.connect(self._show_desktop)

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

    def _show_desktop(self) -> None:
        """Replace login content only after successful backend authentication."""
        self.desktop_view_model = DesktopViewModel(self.backend, self.task_runner)
        self.desktop_window = MainWindow(
            self.qt_application,
            self.desktop_view_model,
            application_name=self.settings.application.name,
        )
        self.desktop_window.return_to_login.connect(self._return_to_login)
        self.login_window.hide()
        self.desktop_window.show()
        self.main_window = self.desktop_window

    def _return_to_login(self) -> None:
        """Dispose decrypted presentation state and show a clean login window."""
        if self.desktop_window is not None:
            self.desktop_window.deleteLater()
        self.desktop_window = None
        self.desktop_view_model = None
        self.login_window.password_input.clear()
        self.login_window.show()
        self.main_window = self.login_window


def create_application(
    arguments: Sequence[str],
    settings: ClientSettings | None = None,
    backend: UiBackend | None = None,
) -> ClientApplication:
    """Create an independently testable desktop application instance."""
    return ClientApplication(arguments, settings, backend)
