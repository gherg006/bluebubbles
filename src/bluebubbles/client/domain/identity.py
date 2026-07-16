"""Immutable client identity values that contain no private key material."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ClientIdentity:
    """Identify the authenticated user and current device."""

    user_id: UUID
    session_id: UUID
    device_name: str
    display_name: str

    def __post_init__(self) -> None:
        if not self.device_name.strip() or not self.display_name.strip():
            raise ValueError("Device and display names are required")
