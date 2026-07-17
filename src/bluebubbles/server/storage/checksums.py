"""Bounded-memory SHA-256 helpers for encrypted attachment bytes."""

from __future__ import annotations

import hashlib
import hmac
from collections.abc import AsyncIterator, Iterable


class ChecksumService:
    """Calculate and compare SHA-256 digests without retaining complete files."""

    @staticmethod
    def digest(data: bytes) -> bytes:
        """Return the SHA-256 digest of one bounded block."""
        return hashlib.sha256(data).digest()

    @staticmethod
    def verify(expected: bytes, actual: bytes) -> bool:
        """Compare digests in constant time."""
        return hmac.compare_digest(expected, actual)

    @staticmethod
    def hash_blocks(blocks: Iterable[bytes]) -> bytes:
        """Hash an ordered synchronous stream of blocks."""
        hasher = hashlib.sha256()
        for block in blocks:
            hasher.update(block)
        return hasher.digest()

    @staticmethod
    async def hash_stream(blocks: AsyncIterator[bytes]) -> bytes:
        """Hash an ordered asynchronous stream of blocks."""
        hasher = hashlib.sha256()
        async for block in blocks:
            hasher.update(block)
        return hasher.digest()
