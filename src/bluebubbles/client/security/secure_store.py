"""Windows Credential Manager storage for small client session secrets."""

from __future__ import annotations

import asyncio
import ctypes
import os
from ctypes import wintypes
from typing import Protocol
from uuid import UUID

from bluebubbles.shared.errors.exceptions import LocalStorageError

_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168
_MAX_CREDENTIAL_BLOB = 2560


class SecureStore(Protocol):
    """Store small protected values through operating-system facilities."""

    async def set_secret(self, key: str, value: bytes) -> None: ...

    async def get_secret(self, key: str) -> bytes | None: ...

    async def delete_secret(self, key: str) -> None: ...

    async def delete_profile(self, profile_id: UUID) -> None: ...


class _CredentialAttributeW(ctypes.Structure):
    _fields_ = [
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class _CredentialW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CredentialAttributeW)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialManagerStore:
    """Store exact binary secrets in the current Windows user's credential vault."""

    _PROFILE_KEYS = ("access_token", "refresh_token", "session_id", "device_id")

    def __init__(self, application_namespace: str = "BlueBubbles") -> None:
        if os.name != "nt":
            raise LocalStorageError(
                user_message="Windows protected credential storage is unavailable."
            )
        namespace = application_namespace.strip()
        if not namespace or any(character in namespace for character in '\\/:*?"<>|'):
            raise ValueError("Credential namespace contains unsupported characters")
        self._namespace = namespace

    async def set_secret(self, key: str, value: bytes) -> None:
        """Store one bounded binary value without logging or text conversion."""
        await asyncio.to_thread(self._set_sync, self._target(key), bytes(value))

    async def get_secret(self, key: str) -> bytes | None:
        """Retrieve an exact binary value, returning None when it is absent."""
        return await asyncio.to_thread(self._get_sync, self._target(key))

    async def delete_secret(self, key: str) -> None:
        """Delete one value idempotently from the current user's vault."""
        await asyncio.to_thread(self._delete_sync, self._target(key))

    async def delete_profile(self, profile_id: UUID) -> None:
        """Delete every known session secret belonging to one local profile."""
        await asyncio.gather(
            *(
                self.delete_secret(f"profile:{profile_id}:{name}")
                for name in self._PROFILE_KEYS
            )
        )

    def _target(self, key: str) -> str:
        selected = key.strip()
        if (
            not selected
            or len(selected) > 512
            or any(character in selected for character in "\r\n\x00")
        ):
            raise ValueError("Credential key is invalid")
        return f"{self._namespace}:{selected}"

    @staticmethod
    def _api() -> ctypes.WinDLL:
        return ctypes.WinDLL("Advapi32.dll", use_last_error=True)

    @classmethod
    def _set_sync(cls, target: str, value: bytes) -> None:
        if not value or len(value) > _MAX_CREDENTIAL_BLOB:
            raise ValueError("Credential values must contain 1 to 2560 bytes")
        blob = (ctypes.c_ubyte * len(value)).from_buffer_copy(value)
        credential = _CredentialW()
        credential.Type = _CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.CredentialBlobSize = len(value)
        credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = target
        api = cls._api()
        api.CredWriteW.argtypes = [ctypes.POINTER(_CredentialW), wintypes.DWORD]
        api.CredWriteW.restype = wintypes.BOOL
        if not api.CredWriteW(ctypes.byref(credential), 0):
            raise LocalStorageError(
                user_message="The protected session secret could not be stored."
            )

    @classmethod
    def _get_sync(cls, target: str) -> bytes | None:
        pointer = ctypes.POINTER(_CredentialW)()
        api = cls._api()
        api.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(_CredentialW)),
        ]
        api.CredReadW.restype = wintypes.BOOL
        if not api.CredReadW(target, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == _ERROR_NOT_FOUND:
                return None
            raise LocalStorageError(
                user_message="The protected session secret could not be read."
            )
        try:
            credential = pointer.contents
            return ctypes.string_at(
                credential.CredentialBlob, credential.CredentialBlobSize
            )
        finally:
            api.CredFree(pointer)

    @classmethod
    def _delete_sync(cls, target: str) -> None:
        api = cls._api()
        api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        api.CredDeleteW.restype = wintypes.BOOL
        if (
            not api.CredDeleteW(target, _CRED_TYPE_GENERIC, 0)
            and ctypes.get_last_error() != _ERROR_NOT_FOUND
        ):
            raise LocalStorageError(
                user_message="The protected session secret could not be deleted."
            )
