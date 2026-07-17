"""Desktop client dependency construction and environment checks."""

from uuid import UUID

from bluebubbles.client.configuration.settings import ClientSettings
from bluebubbles.client.container import ClientContainer
from bluebubbles.client.security.secure_store import SecureStore
from bluebubbles.client.storage.service import LocalStorageService


def build_unauthenticated_container(settings: ClientSettings) -> ClientContainer:
    """Construct the installation-scoped container used before authentication."""
    return ClientContainer(settings)


def build_authenticated_container(
    settings: ClientSettings,
    profile_id: UUID,
    secure_store: SecureStore,
) -> ClientContainer:
    """Construct a disposable user-specific local-storage container."""
    return ClientContainer(
        settings,
        LocalStorageService(profile_id, settings.storage, secure_store),
    )


def verify_client_environment(settings: ClientSettings) -> None:
    """Verify configured client paths are absolute after user-directory expansion."""
    if not settings.storage.profile_root.expanduser().is_absolute():
        raise ValueError("storage.profile_root must be absolute")
    if not settings.transfers.default_download_directory.expanduser().is_absolute():
        raise ValueError("transfers.default_download_directory must be absolute")
