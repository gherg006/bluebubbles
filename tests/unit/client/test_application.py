"""Tests for the desktop-client application factory."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from bluebubbles.client.application import ClientApplication, create_application
from bluebubbles.client.ui.windows import MainWindow
from bluebubbles.version import __version__
from tests.unit.client.test_task_18_viewmodels import FakeBackend, ImmediateTaskRunner


def test_application_factory_configures_qt() -> None:
    application = create_application(["bluebubbles-client"])

    assert isinstance(application, ClientApplication)
    assert application.qt_application.applicationName() == "BlueBubbles"
    assert application.qt_application.applicationVersion() == __version__
    assert application.main_window.windowTitle() == "BlueBubbles"
    assert application.main_window.centralWidget() is not None


def test_factory_reuses_existing_qt_application() -> None:
    first = create_application(["bluebubbles-client"])
    second = create_application(["bluebubbles-client"])

    assert second.qt_application is first.qt_application


def test_run_shows_window_and_returns_event_loop_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = create_application(["bluebubbles-client"])
    monkeypatch.setattr(application.qt_application, "exec", lambda: 7)

    result = application.run()

    assert result == 7
    assert application.main_window.isVisible()
    assert application.container.closed
    application.main_window.hide()


def test_authenticated_shell_replaces_login_and_cleans_up() -> None:
    application = create_application(["bluebubbles-client"], backend=FakeBackend())
    application.task_runner = ImmediateTaskRunner()  # type: ignore[assignment]
    application.login_window.password_input.setText("secret")
    application._show_desktop()
    assert isinstance(application.main_window, MainWindow)
    assert application.desktop_view_model is not None
    application._return_to_login()
    assert type(application.main_window).__name__ == "LoginWindow"
    assert application.login_window.password_input.text() == ""
