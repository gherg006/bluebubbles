"""Focused encrypted attachment filesystem storage evidence."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from bluebubbles.server.storage import (
    AttachmentPathBuilder,
    ChecksumService,
    LocalFileStorage,
)


@pytest.mark.asyncio
async def test_atomic_chunk_write_resume_finalise_and_stream(tmp_path: Path) -> None:
    root = tmp_path / "permanent"
    temporary = tmp_path / "temporary"
    root.mkdir()
    temporary.mkdir()
    paths = AttachmentPathBuilder(root, temporary)
    storage = LocalFileStorage(paths, ChecksumService())
    upload_id = uuid4()
    attachment_id = uuid4()
    await storage.create_upload_area(upload_id)
    stored = await storage.write_chunk(upload_id, 0, b"opaque-ciphertext")
    assert stored.checksum == ChecksumService.digest(b"opaque-ciphertext")
    assert await storage.chunk_exists(upload_id, 0)
    assert (
        b"".join([block async for block in storage.read_upload_chunk(upload_id, 0)])
        == b"opaque-ciphertext"
    )
    reference = await storage.finalise_upload(upload_id, attachment_id)
    assert Path(reference).is_relative_to(root.resolve())
    assert (
        b"".join(
            [block async for block in storage.read_attachment_chunk(attachment_id, 0)]
        )
        == b"opaque-ciphertext"
    )
    await storage.delete_attachment(attachment_id)
    assert not Path(reference).exists()


def test_uuid_paths_remain_inside_configured_roots(tmp_path: Path) -> None:
    root = tmp_path / "root"
    temporary = tmp_path / "temporary"
    paths = AttachmentPathBuilder(root, temporary)
    assert paths.attachment_chunk_path(uuid4(), 7).is_relative_to(root.resolve())
    with pytest.raises(ValueError):
        paths.upload_chunk_path(uuid4(), -1)
