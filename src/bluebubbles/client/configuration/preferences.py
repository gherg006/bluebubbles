"""Validated authenticated-user preferences kept separate from installation settings."""

from pathlib import Path
from typing import Annotated

from pydantic import Field

from bluebubbles.shared._model import ContractModel


class NotificationPreferences(ContractModel):
    """Define user-controlled desktop notification behaviour."""

    enabled: bool = True
    play_sound: bool = True
    show_previews: bool = False


class AppearancePreferences(ContractModel):
    """Define user-controlled appearance choices."""

    theme: str = "system"
    font_scale: Annotated[float, Field(ge=0.75, le=2.0)] = 1.0
    reduced_motion: bool = False


class TransferPreferences(ContractModel):
    """Define user-controlled transfer limits."""

    download_directory: Path = Path.home() / "Downloads" / "BlueBubbles"
    upload_bandwidth_limit: Annotated[int, Field(gt=0)] | None = None
    download_bandwidth_limit: Annotated[int, Field(gt=0)] | None = None


class UserPreferences(ContractModel):
    """Represent user choices that server policy may constrain."""

    appearance: AppearancePreferences = Field(default_factory=AppearancePreferences)
    notifications: NotificationPreferences = Field(
        default_factory=NotificationPreferences
    )
    transfers: TransferPreferences = Field(default_factory=TransferPreferences)
    cache_limit_bytes: Annotated[int, Field(gt=0)] = 1_073_741_824
    close_to_tray: bool = True
    send_with_enter: bool = True
    show_message_previews: bool = False
