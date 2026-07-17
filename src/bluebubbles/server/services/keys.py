"""Versioned public identity-key registration and retrieval."""

import base64
import binascii
import hmac
from datetime import UTC, datetime
from uuid import UUID, uuid4

from bluebubbles.server.database.unit_of_work import UnitOfWorkFactory
from bluebubbles.server.domain.audit import AuditSeverity
from bluebubbles.server.domain.outbox import OutboxEvent
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.domain.users import PublicKeyRecord
from bluebubbles.server.services.audit import AuthenticationAuditWriter
from bluebubbles.shared.errors.exceptions import ConflictError, ResourceNotFoundError
from bluebubbles.shared.models.users import PublicUserKeyResponse
from bluebubbles.shared.security.fingerprints import calculate_public_key_fingerprint
from bluebubbles.shared.security.key_models import (
    KeyFingerprint,
    KeyVersion,
    PublicKeyAlgorithm,
    PublicKeyDescriptor,
    PublicKeyType,
    RegisterPublicKeyRequest,
    RevokePublicKeyRequest,
)

_ALGORITHM_FOR_TYPE = {
    PublicKeyType.ENCRYPTION: PublicKeyAlgorithm.X25519_V1,
    PublicKeyType.SIGNING: PublicKeyAlgorithm.ED25519_V1,
}


class PublicKeyService:
    """Validate, rotate, and expose public-only identity keys."""

    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        audit_writer: AuthenticationAuditWriter,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._audit_writer = audit_writer

    async def register(
        self, requester: AuthenticatedUser, request: RegisterPublicKeyRequest
    ) -> PublicKeyDescriptor:
        """Register the next independent key revision for the current user."""
        if request.algorithm is not _ALGORITHM_FOR_TYPE[request.key_type]:
            raise ConflictError(
                user_message="The key algorithm does not match its purpose."
            )
        try:
            raw_key = base64.b64decode(request.public_key, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ConflictError(
                user_message="The public key encoding is invalid."
            ) from error
        expected_fingerprint = calculate_public_key_fingerprint(
            raw_key,
            algorithm=request.algorithm.value,
            key_type=request.key_type.value,
            key_version=request.version.value,
        )
        if not hmac.compare_digest(expected_fingerprint, request.fingerprint.value):
            raise ConflictError(
                user_message="The public key fingerprint does not match."
            )
        now = datetime.now(UTC)
        if request.expires_at is not None and (
            request.expires_at.tzinfo is None or request.expires_at <= now
        ):
            raise ConflictError(
                user_message="A new public key must expire in the future."
            )
        async with self._unit_of_work_factory() as unit_of_work:
            user = await unit_of_work.users.get_by_id(requester.user_id)
            if user is None or not user.is_enabled:
                raise ResourceNotFoundError()
            existing = await unit_of_work.public_keys.get_version(
                requester.user_id,
                key_type=request.key_type.value,
                key_version=request.version.value,
            )
            if existing is not None:
                if (
                    existing.public_key == raw_key
                    and existing.fingerprint == expected_fingerprint
                ):
                    return self._descriptor(existing)
                raise ConflictError(
                    user_message="That key version is already registered."
                )
            active = await unit_of_work.public_keys.get_active(
                requester.user_id, key_type=request.key_type.value
            )
            if active is not None:
                expected_version = active.key_version + 1
            else:
                history = await unit_of_work.public_keys.list_for_user(
                    requester.user_id
                )
                latest_version = max(
                    (
                        key.key_version
                        for key in history
                        if key.key_type == request.key_type.value
                    ),
                    default=0,
                )
                expected_version = latest_version + 1
            if request.version.value != expected_version:
                raise ConflictError(
                    user_message="Public key versions must increase by one."
                )
            record = PublicKeyRecord(
                id=uuid4(),
                created_at=now,
                updated_at=now,
                user_id=requester.user_id,
                key_type=request.key_type.value,
                key_version=request.version.value,
                algorithm=request.algorithm.value,
                public_key=raw_key,
                fingerprint=expected_fingerprint,
                expires_at=request.expires_at,
            )
            await unit_of_work.public_keys.add(record)
            await unit_of_work.outbox.add(
                OutboxEvent(
                    id=uuid4(),
                    created_at=record.created_at,
                    updated_at=record.created_at,
                    event_type="KEY_CHANGED",
                    aggregate_type="user",
                    aggregate_id=requester.user_id,
                    protocol_version=1,
                    payload={
                        "user_id": str(requester.user_id),
                        "key_type": request.key_type.value,
                        "key_version": request.version.value,
                        "fingerprint": expected_fingerprint,
                        "changed_at": record.created_at.isoformat(),
                    },
                    available_at=record.created_at,
                )
            )
            await self._audit_writer.append(
                unit_of_work.audit,
                event_type="public_key_registered",
                occurred_at=record.created_at,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.INFORMATIONAL,
                details={
                    "key_type": request.key_type.value,
                    "key_version": request.version.value,
                    "fingerprint": expected_fingerprint,
                },
            )
            await unit_of_work.commit()
        return self._descriptor(record)

    async def list_for_user(self, user_id: UUID) -> PublicUserKeyResponse:
        """Return retained public-key history for a visible enabled user."""
        async with self._unit_of_work_factory() as unit_of_work:
            user = await unit_of_work.users.get_by_id(user_id)
            if user is None or not user.is_enabled:
                raise ResourceNotFoundError()
            keys = await unit_of_work.public_keys.list_for_user(user_id)
        return PublicUserKeyResponse(
            user_id=user_id, keys=tuple(self._descriptor(key) for key in keys)
        )

    async def revoke(
        self,
        requester: AuthenticatedUser,
        key_id: UUID,
        request: RevokePublicKeyRequest,
    ) -> None:
        """Revoke one key owned by the requester and durably notify clients."""
        now = datetime.now(UTC)
        async with self._unit_of_work_factory() as unit_of_work:
            key = await unit_of_work.public_keys.get_by_id(key_id)
            if key is None or key.user_id != requester.user_id:
                raise ResourceNotFoundError()
            if key.revoked_at is not None:
                return
            if not await unit_of_work.public_keys.revoke(key.id, now, request.reason):
                raise ConflictError(user_message="The public key could not be revoked.")
            await unit_of_work.outbox.add(
                OutboxEvent(
                    id=uuid4(),
                    created_at=now,
                    updated_at=now,
                    event_type="KEY_CHANGED",
                    aggregate_type="user",
                    aggregate_id=requester.user_id,
                    protocol_version=1,
                    payload={
                        "user_id": str(requester.user_id),
                        "key_type": key.key_type,
                        "key_version": key.key_version,
                        "fingerprint": key.fingerprint,
                        "changed_at": now.isoformat(),
                    },
                    available_at=now,
                )
            )
            await self._audit_writer.append(
                unit_of_work.audit,
                event_type="public_key_revoked",
                occurred_at=now,
                actor_id=requester.user_id,
                source_ip=None,
                severity=AuditSeverity.WARNING,
                details={
                    "key_id": str(key.id),
                    "key_type": key.key_type,
                    "key_version": key.key_version,
                    "reason": request.reason,
                },
            )
            await unit_of_work.commit()

    @staticmethod
    def _descriptor(record: PublicKeyRecord) -> PublicKeyDescriptor:
        return PublicKeyDescriptor(
            owner_id=record.user_id,
            key_type=PublicKeyType(record.key_type),
            version=KeyVersion(value=record.key_version),
            algorithm=PublicKeyAlgorithm(record.algorithm),
            public_key=base64.b64encode(record.public_key).decode("ascii"),
            fingerprint=KeyFingerprint(value=record.fingerprint),
            created_at=record.created_at,
            expires_at=record.expires_at,
            revoked_at=record.revoked_at,
            is_primary=record.is_primary,
        )
