"""Semantic application and integer protocol-version compatibility helpers."""

import re
from collections.abc import Collection
from dataclasses import dataclass
from functools import total_ordering

_SEMANTIC_VERSION = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@total_ordering
@dataclass(frozen=True, slots=True, eq=False)
class SemanticVersion:
    """Represent one validated Semantic Version 2.0 value."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("Version numbers cannot be negative")
        for identifier in self.prerelease:
            if (
                identifier.isdigit()
                and len(identifier) > 1
                and identifier.startswith("0")
            ):
                raise ValueError(
                    "Numeric prerelease identifiers cannot have leading zeros"
                )

    def __str__(self) -> str:
        value = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            value += "-" + ".".join(self.prerelease)
        if self.build:
            value += "+" + ".".join(self.build)
        return value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        left = (self.major, self.minor, self.patch)
        right = (other.major, other.minor, other.patch)
        if left != right:
            return left < right
        return self._prerelease_key() < other._prerelease_key()

    def __eq__(self, other: object) -> bool:
        """Compare semantic precedence; build metadata is intentionally ignored."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return (
            self.major,
            self.minor,
            self.patch,
            self.prerelease,
        ) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )

    def __hash__(self) -> int:
        """Hash the same precedence fields used by equality."""
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def _prerelease_key(self) -> tuple[tuple[int, int | str], ...]:
        if not self.prerelease:
            return ((2, ""),)
        return tuple(
            (0, int(part)) if part.isdigit() else (1, part) for part in self.prerelease
        )


@dataclass(frozen=True, order=True, slots=True)
class ProtocolVersion:
    """Represent a positive protocol generation number."""

    value: int

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or self.value < 1:
            raise ValueError("Protocol version must be a positive integer")

    def __str__(self) -> str:
        return str(self.value)


def parse_version(value: str) -> SemanticVersion:
    """Parse a strict Semantic Version 2.0 string.

    Raises:
        ValueError: If ``value`` is malformed.
    """
    match = _SEMANTIC_VERSION.fullmatch(value)
    if match is None:
        raise ValueError(f"Malformed semantic version: {value!r}")
    return SemanticVersion(
        int(match["major"]),
        int(match["minor"]),
        int(match["patch"]),
        tuple((match["prerelease"] or "").split(".")) if match["prerelease"] else (),
        tuple((match["build"] or "").split(".")) if match["build"] else (),
    )


def compare_versions(left: str | SemanticVersion, right: str | SemanticVersion) -> int:
    """Return -1, 0, or 1 according to semantic-version precedence."""
    parsed_left = parse_version(left) if isinstance(left, str) else left
    parsed_right = parse_version(right) if isinstance(right, str) else right
    return (parsed_left > parsed_right) - (parsed_left < parsed_right)


def select_highest_common_protocol(
    client_versions: Collection[int | ProtocolVersion],
    server_versions: Collection[int | ProtocolVersion],
) -> ProtocolVersion | None:
    """Return the highest mutually supported protocol, or ``None``."""
    client = {_protocol_value(value) for value in client_versions}
    server = {_protocol_value(value) for value in server_versions}
    common = client & server
    return ProtocolVersion(max(common)) if common else None


def is_client_supported(
    client_version: str | SemanticVersion,
    minimum_version: str | SemanticVersion,
    maximum_major: int | None = None,
) -> bool:
    """Return whether a client meets the minimum and optional major ceiling."""
    client = (
        parse_version(client_version)
        if isinstance(client_version, str)
        else client_version
    )
    minimum = (
        parse_version(minimum_version)
        if isinstance(minimum_version, str)
        else minimum_version
    )
    return client >= minimum and (
        maximum_major is None or client.major <= maximum_major
    )


def _protocol_value(value: int | ProtocolVersion) -> int:
    return ProtocolVersion(value).value if isinstance(value, int) else value.value
