"""Versioned server configuration change value objects."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConfigurationRevision:
    """Record a safe summary of one validated configuration change."""

    revision: int
    changed_at: datetime
    changed_by: UUID
    changed_keys: frozenset[str]
    public_values: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.revision < 1 or self.changed_at.tzinfo is None:
            raise ValueError("Configuration revision and aware timestamp are required")
        forbidden = {
            key
            for key in self.public_values
            if "secret" in key.casefold() or "password" in key.casefold()
        }
        if forbidden:
            raise ValueError("Configuration revision cannot contain secret values")
        object.__setattr__(
            self, "public_values", MappingProxyType(dict(self.public_values))
        )
