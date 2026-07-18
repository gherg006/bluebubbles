"""Task 16 Windows protected credential adapter boundary tests."""

from __future__ import annotations

import ctypes
from uuid import uuid4

import pytest

from bluebubbles.client.security.secure_store import WindowsCredentialManagerStore
from bluebubbles.shared.errors.exceptions import LocalStorageError


class Function:
    """Act like a ctypes function while accepting argtype assignment."""

    def __init__(self, result: bool) -> None:
        self.result = result
        self.argtypes: object = None
        self.restype: object = None
        self.calls = 0

    def __call__(self, *args: object) -> bool:
        del args
        self.calls += 1
        return self.result


class Api:
    """Expose the subset of Advapi32 used by write and delete tests."""

    def __init__(self, write: bool = True, delete: bool = True) -> None:
        self.CredWriteW = Function(write)
        self.CredDeleteW = Function(delete)


def test_namespace_target_and_value_validation() -> None:
    with pytest.raises(ValueError):
        WindowsCredentialManagerStore("bad/name")
    store = WindowsCredentialManagerStore("TestBlueBubbles")
    assert store._target(" key ") == "TestBlueBubbles:key"
    with pytest.raises(ValueError):
        store._target("\n")
    with pytest.raises(ValueError):
        store._target("x" * 513)
    with pytest.raises(ValueError):
        store._set_sync("target", b"")
    with pytest.raises(ValueError):
        store._set_sync("target", b"x" * 2561)


def test_credential_write_and_delete_api_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    successful = Api()
    monkeypatch.setattr(
        WindowsCredentialManagerStore, "_api", staticmethod(lambda: successful)
    )
    WindowsCredentialManagerStore._set_sync("target", b"secret")
    assert successful.CredWriteW.calls == 1
    WindowsCredentialManagerStore._delete_sync("target")
    assert successful.CredDeleteW.calls == 1
    failed_write = Api(write=False)
    monkeypatch.setattr(
        WindowsCredentialManagerStore, "_api", staticmethod(lambda: failed_write)
    )
    with pytest.raises(LocalStorageError):
        WindowsCredentialManagerStore._set_sync("target", b"secret")
    failed_delete = Api(delete=False)
    monkeypatch.setattr(
        WindowsCredentialManagerStore, "_api", staticmethod(lambda: failed_delete)
    )
    ctypes.set_last_error(5)
    with pytest.raises(LocalStorageError):
        WindowsCredentialManagerStore._delete_sync("target")


@pytest.mark.asyncio
async def test_profile_deletion_targets_every_known_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = WindowsCredentialManagerStore("TestBlueBubbles")
    deleted: list[str] = []

    async def delete(key: str) -> None:
        deleted.append(key)

    monkeypatch.setattr(store, "delete_secret", delete)
    profile_id = uuid4()
    await store.delete_profile(profile_id)
    assert len(deleted) == 5
    assert all(str(profile_id) in key for key in deleted)
