"""Strict, secret-free release and backup manifest contracts."""

import re
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated

from pydantic import Field, field_validator, model_validator

from bluebubbles.shared._model import ContractModel

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _validate_aware_datetime(value: datetime) -> datetime:
    """Require an offset-aware timestamp for operational evidence."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return value


def _validate_relative_artifact_path(value: str) -> str:
    """Accept one canonical POSIX path contained by a release root."""
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or value != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("artifact path must be a canonical relative POSIX path")
    return value


class BackupResult(StrEnum):
    """Describe the final state of one coordinated backup."""

    SUCCESS = "success"
    FAILED = "failed"


class ArtifactRecord(ContractModel):
    """Record the size and SHA-256 digest of one release artifact."""

    path: str
    size_bytes: Annotated[int, Field(ge=0)]
    sha256: str

    _path_is_safe = field_validator("path")(_validate_relative_artifact_path)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        """Require a lower-case SHA-256 hexadecimal digest."""
        if not _SHA256_PATTERN.fullmatch(value):
            raise ValueError("sha256 must contain 64 lower-case hexadecimal characters")
        return value


class ReleaseManifest(ContractModel):
    """Describe a complete, independently verifiable server release."""

    application_version: str
    protocol_version: Annotated[int, Field(gt=0)]
    database_revision: str
    configuration_version: Annotated[int, Field(gt=0)]
    created_at: datetime
    created_by: str
    artifacts: tuple[ArtifactRecord, ...]

    _created_at_is_aware = field_validator("created_at")(_validate_aware_datetime)

    @field_validator("application_version", "database_revision", "created_by")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        """Reject blank, oversized, or control-bearing manifest identifiers."""
        if not _IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError("manifest identifier contains unsupported characters")
        return value

    @model_validator(mode="after")
    def validate_artifact_set(self) -> "ReleaseManifest":
        """Require at least one artifact and prohibit duplicate paths."""
        paths = [artifact.path for artifact in self.artifacts]
        if not paths:
            raise ValueError("release manifest must contain at least one artifact")
        if len(paths) != len(set(paths)):
            raise ValueError("release manifest artifact paths must be unique")
        return self


class BackupManifest(ContractModel):
    """Record coordinated backup inputs and verification evidence."""

    backup_id: str
    started_at: datetime
    completed_at: datetime
    application_version: str
    database_revision: str
    database: BackupResult
    attachments: BackupResult
    configuration: BackupResult
    verification: BackupResult
    artifacts: tuple[ArtifactRecord, ...]
    warnings: tuple[str, ...] = ()

    _started_at_is_aware = field_validator("started_at")(_validate_aware_datetime)
    _completed_at_is_aware = field_validator("completed_at")(_validate_aware_datetime)

    @field_validator("backup_id", "application_version", "database_revision")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        """Require a log-safe identifier suitable for a directory name."""
        if not _IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError("backup identifier contains unsupported characters")
        return value

    @field_validator("warnings")
    @classmethod
    def validate_warnings(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Keep warning evidence bounded and single-line."""
        if len(values) > 100 or any(
            not value or len(value) > 500 or "\n" in value or "\r" in value
            for value in values
        ):
            raise ValueError("backup warnings must be bounded non-empty single lines")
        return values

    @model_validator(mode="after")
    def validate_result(self) -> "BackupManifest":
        """Ensure successful evidence is chronological and fully verified."""
        if self.completed_at < self.started_at:
            raise ValueError("backup completion cannot precede its start")
        component_results = (
            self.database,
            self.attachments,
            self.configuration,
            self.verification,
        )
        if not self.artifacts and all(
            result is BackupResult.SUCCESS for result in component_results
        ):
            raise ValueError("a successful backup must record verified artifacts")
        paths = [artifact.path for artifact in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("backup manifest artifact paths must be unique")
        return self
