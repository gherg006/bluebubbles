"""Approved, versioned, secret-free administrative configuration changes."""

from collections.abc import Callable, Mapping
from datetime import UTC, datetime

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.configuration import ConfigurationRevision
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import Permission
from bluebubbles.server.services.audit import AuditWriter
from bluebubbles.server.services.permissions import PermissionService
from bluebubbles.shared.errors.exceptions import ConflictError, ValidationError
from bluebubbles.shared.models.administration import ConfigurationSummary

_APPROVED_FIELDS = frozenset(
    {
        "messaging.edit_window_seconds",
        "messaging.read_receipts_enabled",
        "messaging.typing_indicators_enabled",
        "features.message_editing",
        "features.read_receipts",
        "features.typing_indicators",
        "features.attachment_uploads",
        "rate_limits.administration_requests_per_minute",
    }
)
_RESTART_REQUIRED_FIELDS = frozenset({"features.attachment_uploads"})


class ConfigurationService:
    """Validate an allowlist and append a public configuration revision."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        permission_service: PermissionService,
        audit_writer: AuditWriter | None = None,
        apply_reloadable: Callable[[Mapping[str, object]], None] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._uow_factory = unit_of_work_factory
        self._permissions = permission_service
        self._audit = audit_writer or AuditWriter()
        self._apply_reloadable = apply_reloadable
        self._clock = clock

    async def latest(self, requester: AuthenticatedUser) -> ConfigurationSummary:
        """Return only the newest persisted public configuration values."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.CONFIGURATION_VIEW
        )
        async with self._uow_factory() as uow:
            revision = await uow.configuration.get_latest()
        if revision is None:
            return ConfigurationSummary(revision=1, values={}, updated_at=self._clock())
        return self._summary(revision)

    async def history(
        self, requester: AuthenticatedUser, *, limit: int = 50
    ) -> tuple[ConfigurationSummary, ...]:
        """Return a bounded newest-first secret-free revision history."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.CONFIGURATION_VIEW
        )
        async with self._uow_factory() as uow:
            history = await uow.configuration.list_history(limit=limit)
        return tuple(self._summary(revision) for revision in history)

    async def update(
        self,
        requester: AuthenticatedUser,
        *,
        expected_revision: int,
        values: Mapping[str, object],
        reason: str,
    ) -> ConfigurationSummary:
        """Append an approved revision and apply reloadable keys after commit."""
        await self._permissions.require_authenticated_permission(
            requester, Permission.CONFIGURATION_MODIFY
        )
        reason = reason.strip()
        if not reason or len(reason) > 1000:
            raise ValidationError(
                user_message="A configuration change reason is required."
            )
        unknown = set(values) - _APPROVED_FIELDS
        if unknown or any(
            marker in key.casefold()
            for key in values
            for marker in ("secret", "password", "token", "url", "private")
        ):
            raise ValidationError(
                user_message="One or more configuration fields cannot be changed here."
            )
        self._validate_values(values)
        now = self._clock()
        async with self._uow_factory() as uow:
            latest = await uow.configuration.get_latest()
            current_number = latest.revision if latest is not None else 0
            if current_number != expected_revision:
                raise ConflictError(
                    user_message=(
                        "The configuration changed before this update was saved."
                    )
                )
            public_values = dict(latest.public_values if latest is not None else {})
            public_values.update(values)
            revision = ConfigurationRevision(
                revision=current_number + 1,
                changed_at=now,
                changed_by=requester.user_id,
                changed_keys=frozenset(values),
                public_values=public_values,
            )
            restart_required = bool(set(values) & _RESTART_REQUIRED_FIELDS)
            await uow.configuration.append(
                revision, reason=reason, restart_required=restart_required
            )
            await self._audit.append(
                uow.audit,
                event_type="configuration.updated",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={
                    "changed_keys": sorted(values),
                    "reason": reason,
                    "restart_required": restart_required,
                },
            )
            await uow.commit()
        reloadable = {
            key: value
            for key, value in values.items()
            if key not in _RESTART_REQUIRED_FIELDS
        }
        if reloadable and self._apply_reloadable is not None:
            self._apply_reloadable(reloadable)
        return self._summary(revision)

    @staticmethod
    def _validate_values(values: Mapping[str, object]) -> None:
        for key, value in values.items():
            if key.endswith("_enabled") or key.startswith("features."):
                if not isinstance(value, bool):
                    raise ValidationError(user_message=f"{key} must be true or false.")
            elif not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValidationError(
                    user_message=f"{key} must be a non-negative integer."
                )

    @staticmethod
    def _summary(revision: ConfigurationRevision) -> ConfigurationSummary:
        values = {
            key: value
            for key, value in revision.public_values.items()
            if isinstance(value, str | int | float | bool) or value is None
        }
        return ConfigurationSummary(
            revision=revision.revision,
            values=values,
            updated_at=revision.changed_at,
        )
