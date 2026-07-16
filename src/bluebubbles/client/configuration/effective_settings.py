"""Resolve installation defaults, user preferences, and authoritative policy."""

from dataclasses import dataclass
from pathlib import Path

from bluebubbles.client.configuration.policies import ClientPolicy
from bluebubbles.client.configuration.preferences import UserPreferences
from bluebubbles.client.configuration.settings import ClientSettings


@dataclass(frozen=True, slots=True)
class EffectiveClientSettings:
    """Contain resolved user-facing values and any policy overrides."""

    cache_limit_bytes: int
    download_directory: Path
    show_message_previews: bool
    read_receipts_enabled: bool
    overridden_preferences: tuple[str, ...]


class EffectiveSettingsResolver:
    """Apply server restrictions without mutating installation or user settings."""

    def resolve(
        self,
        installation: ClientSettings,
        preferences: UserPreferences,
        policy: ClientPolicy,
    ) -> EffectiveClientSettings:
        """Return effective settings and identify preferences constrained by policy."""
        allowed_cache = min(
            installation.storage.maximum_cache_limit_bytes,
            policy.maximum_cache_bytes,
        )
        effective_cache = min(preferences.cache_limit_bytes, allowed_cache)
        overridden: list[str] = []
        if effective_cache != preferences.cache_limit_bytes:
            overridden.append("cache_limit_bytes")
        previews = preferences.show_message_previews and policy.decrypted_cache_allowed
        if previews != preferences.show_message_previews:
            overridden.append("show_message_previews")
        return EffectiveClientSettings(
            cache_limit_bytes=effective_cache,
            download_directory=preferences.transfers.download_directory,
            show_message_previews=previews,
            read_receipts_enabled=policy.read_receipts_enabled,
            overridden_preferences=tuple(overridden),
        )
