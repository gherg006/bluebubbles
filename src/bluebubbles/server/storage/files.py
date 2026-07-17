"""Safe local storage for opaque encrypted attachment chunks."""

from __future__ import annotations

import asyncio
import os
import shutil
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from bluebubbles.server.storage.checksums import ChecksumService
from bluebubbles.shared.errors.exceptions import StorageError


@dataclass(frozen=True, slots=True)
class StoredChunk:
    """Describe one atomically stored encrypted chunk."""

    size: int
    checksum: bytes
    reference: str


class AttachmentPathBuilder:
    """Build UUID-only paths and enforce configured-root containment."""

    def __init__(self, root_path: Path, temporary_path: Path) -> None:
        self.root = root_path.resolve()
        self.temporary = temporary_path.resolve()

    def upload_directory(self, upload_id: UUID) -> Path:
        return self.verify_contained(
            self.temporary / "uploads" / str(upload_id), self.temporary
        )

    def upload_chunk_path(self, upload_id: UUID, chunk_index: int) -> Path:
        if chunk_index < 0:
            raise ValueError("Chunk index cannot be negative")
        return self.verify_contained(
            self.upload_directory(upload_id) / "chunks" / f"{chunk_index:08d}.chunk",
            self.temporary,
        )

    def attachment_directory(self, attachment_id: UUID) -> Path:
        return self.verify_contained(
            self.root / "attachments" / str(attachment_id), self.root
        )

    def attachment_chunk_path(self, attachment_id: UUID, chunk_index: int) -> Path:
        if chunk_index < 0:
            raise ValueError("Chunk index cannot be negative")
        return self.verify_contained(
            self.attachment_directory(attachment_id) / f"{chunk_index:08d}.chunk",
            self.root,
        )

    @staticmethod
    def verify_contained(path: Path, root: Path) -> Path:
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise StorageError(user_message="The attachment storage path is invalid.")
        return resolved


class FileStorage(ABC):
    """Define storage operations for ciphertext-only attachment chunks."""

    @abstractmethod
    async def create_upload_area(self, upload_id: UUID) -> None: ...

    @abstractmethod
    async def write_chunk(
        self, upload_id: UUID, chunk_index: int, data: bytes
    ) -> StoredChunk: ...

    @abstractmethod
    def read_upload_chunk(
        self, upload_id: UUID, chunk_index: int
    ) -> AsyncIterator[bytes]: ...

    @abstractmethod
    def read_attachment_chunk(
        self, attachment_id: UUID, chunk_index: int
    ) -> AsyncIterator[bytes]: ...

    @abstractmethod
    async def chunk_exists(self, upload_id: UUID, chunk_index: int) -> bool: ...

    @abstractmethod
    async def finalise_upload(self, upload_id: UUID, attachment_id: UUID) -> str: ...

    @abstractmethod
    async def delete_upload(self, upload_id: UUID) -> None: ...

    @abstractmethod
    async def delete_attachment(self, attachment_id: UUID) -> None: ...

    @abstractmethod
    async def get_free_bytes(self) -> int: ...


class LocalFileStorage(FileStorage):
    """Store encrypted chunks under generated, root-contained local paths."""

    def __init__(
        self, paths: AttachmentPathBuilder, checksums: ChecksumService
    ) -> None:
        self._paths = paths
        self._checksums = checksums

    async def create_upload_area(self, upload_id: UUID) -> None:
        directory = self._paths.upload_directory(upload_id) / "chunks"
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)

    async def write_chunk(
        self, upload_id: UUID, chunk_index: int, data: bytes
    ) -> StoredChunk:
        if not data:
            raise ValueError("Encrypted chunk cannot be empty")
        target = self._paths.upload_chunk_path(upload_id, chunk_index)
        await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
        checksum = self._checksums.digest(data)

        def write() -> None:
            temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
            try:
                with temporary.open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)

        try:
            await asyncio.to_thread(write)
        except OSError as error:
            raise StorageError(
                user_message="The encrypted chunk could not be stored."
            ) from error
        return StoredChunk(len(data), checksum, str(target))

    async def read_upload_chunk(
        self, upload_id: UUID, chunk_index: int
    ) -> AsyncIterator[bytes]:
        async for block in self._read(
            self._paths.upload_chunk_path(upload_id, chunk_index)
        ):
            yield block

    async def read_attachment_chunk(
        self, attachment_id: UUID, chunk_index: int
    ) -> AsyncIterator[bytes]:
        async for block in self._read(
            self._paths.attachment_chunk_path(attachment_id, chunk_index)
        ):
            yield block

    async def chunk_exists(self, upload_id: UUID, chunk_index: int) -> bool:
        return await asyncio.to_thread(
            self._paths.upload_chunk_path(upload_id, chunk_index).is_file
        )

    async def finalise_upload(self, upload_id: UUID, attachment_id: UUID) -> str:
        source = self._paths.upload_directory(upload_id) / "chunks"
        target = self._paths.attachment_directory(attachment_id)

        def move() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise FileExistsError("Attachment target already exists")
            os.replace(source, target)
            shutil.rmtree(source.parent, ignore_errors=True)

        try:
            await asyncio.to_thread(move)
        except OSError as error:
            raise StorageError(
                user_message="The attachment could not be finalised."
            ) from error
        return str(target)

    async def delete_upload(self, upload_id: UUID) -> None:
        await asyncio.to_thread(
            shutil.rmtree, self._paths.upload_directory(upload_id), True
        )

    async def delete_attachment(self, attachment_id: UUID) -> None:
        await asyncio.to_thread(
            shutil.rmtree, self._paths.attachment_directory(attachment_id), True
        )

    async def get_free_bytes(self) -> int:
        usage = await asyncio.to_thread(shutil.disk_usage, self._paths.root)
        return usage.free

    @staticmethod
    async def _read(path: Path, block_size: int = 262_144) -> AsyncIterator[bytes]:
        try:
            stream = await asyncio.to_thread(path.open, "rb")
        except OSError as error:
            raise StorageError(
                user_message="The encrypted attachment chunk is unavailable."
            ) from error
        try:
            while block := await asyncio.to_thread(stream.read, block_size):
                yield block
        finally:
            await asyncio.to_thread(stream.close)
