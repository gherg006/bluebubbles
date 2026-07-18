"""HMAC-token local search over authenticated encrypted message previews."""

from __future__ import annotations

import hashlib
import hmac
import re
import sqlite3
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from bluebubbles.client.domain.search import SearchQuery, SearchResult
from bluebubbles.client.security.local_encryption import (
    EncryptedLocalValue,
    LocalEncryptionPurpose,
    LocalEncryptionService,
    LocalKeyProvider,
)
from bluebubbles.client.storage.database import LocalDatabaseManager

_TOKEN_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True, slots=True)
class SearchIndexRecord:
    """Carry one authorised decrypted message into an explicit index rebuild."""

    message_id: UUID
    conversation_id: UUID
    sender_id: UUID
    created_at: datetime
    text: str
    source_version: int = 1


class SearchTokenService:
    """Normalize terms and create profile-secret HMAC-SHA-256 digests."""

    def __init__(self, key_provider: LocalKeyProvider) -> None:
        self._key_provider = key_provider

    def normalise(self, text: str) -> list[str]:
        """Return stable Unicode-normalized, case-folded exact tokens."""
        normalized = unicodedata.normalize("NFKC", text).casefold()
        return _TOKEN_PATTERN.findall(normalized)

    async def token_digest(self, token: str) -> bytes:
        """Return one deterministic keyed token digest for this profile."""
        normalized = self.normalise(token)
        if len(normalized) != 1:
            raise ValueError("Search token must normalize to exactly one word")
        master = await self._key_provider.get_master_key()
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"bluebubbles-local-search-v1",
            info=b"bluebubbles:search-token",
        ).derive(master)
        return hmac.digest(key, normalized[0].encode("utf-8"), hashlib.sha256)


class LocalSearchService:
    """Index and search only plaintext already authorized on this client."""

    def __init__(
        self,
        database: LocalDatabaseManager,
        encryption: LocalEncryptionService,
        token_service: SearchTokenService,
        profile_id: UUID,
    ) -> None:
        self._database = database
        self._encryption = encryption
        self._token_service = token_service
        self._profile_id = profile_id

    async def index_message(
        self,
        message_id: UUID,
        conversation_id: UUID,
        sender_id: UUID,
        created_at: datetime,
        text: str,
        source_version: int = 1,
    ) -> None:
        """Replace one message's encrypted preview and keyed token set atomically."""
        tokens = self._token_service.normalise(text)
        if not tokens:
            await self.remove_message(message_id)
            return
        document_id = uuid4()
        encrypted = await self._encryption.encrypt(
            LocalEncryptionPurpose.SEARCH_INDEX,
            text.encode("utf-8"),
            self._context(message_id, conversation_id),
        )
        digests = [await self._token_service.token_digest(token) for token in tokens]
        indexed_at = datetime.now().astimezone().isoformat()

        def operation(connection: sqlite3.Connection) -> None:
            execute = connection.execute
            executemany = connection.executemany
            execute(
                "DELETE FROM search_documents WHERE source_id = ?", (str(message_id),)
            )
            execute(
                "INSERT INTO search_documents(document_id, source_id, conversation_id, "
                "sender_id, created_at, preview_ciphertext, preview_nonce, "
                "format_version, source_version, indexed_at) VALUES (?, ?, ?, ?, ?, ?, "
                "?, ?, ?, ?)",
                (
                    str(document_id),
                    str(message_id),
                    str(conversation_id),
                    str(sender_id),
                    created_at.isoformat(),
                    encrypted.ciphertext,
                    encrypted.nonce,
                    encrypted.version,
                    source_version,
                    indexed_at,
                ),
            )
            executemany(
                "INSERT INTO search_terms(token_digest, document_id, token_position) "
                "VALUES (?, ?, ?)",
                [
                    (digest, str(document_id), position)
                    for position, digest in enumerate(digests)
                ],
            )
            connection.commit()

        await self._database.run_transaction(operation)

    async def remove_message(self, message_id: UUID) -> None:
        """Remove one document and its cascading token rows."""
        await self._database.execute(
            "DELETE FROM search_documents WHERE source_id = ?", (str(message_id),)
        )

    async def clear_conversation(self, conversation_id: UUID) -> None:
        """Invalidate every search document for one inaccessible conversation."""
        await self._database.execute(
            "DELETE FROM search_documents WHERE conversation_id = ?",
            (str(conversation_id),),
        )

    async def clear(self) -> None:
        """Remove the replaceable private search index."""
        await self._database.execute("DELETE FROM search_documents")

    async def rebuild(self, records: Sequence[SearchIndexRecord]) -> int:
        """Replace the index from explicitly supplied authorised cache content."""
        await self.clear()
        for record in records:
            await self.index_message(
                record.message_id,
                record.conversation_id,
                record.sender_id,
                record.created_at,
                record.text,
                record.source_version,
            )
        return len(records)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Find digest matches and verify actual plaintext candidates in memory."""
        terms = self._token_service.normalise(query.text)
        if not terms:
            raise ValueError("Search query must contain at least one word")
        digests = list(
            dict.fromkeys(
                [await self._token_service.token_digest(term) for term in terms]
            )
        )
        candidate_ids: set[str] | None = None
        for digest in digests:
            token_rows = await self._database.fetch_all(
                "SELECT document_id FROM search_terms WHERE token_digest = ?",
                (digest,),
            )
            matches = {str(row[0]) for row in token_rows}
            candidate_ids = (
                matches if candidate_ids is None else candidate_ids & matches
            )
        rows = []
        for document_id in candidate_ids or set():
            row = await self._database.fetch_one(
                "SELECT source_id, conversation_id, created_at, preview_ciphertext, "
                "preview_nonce, format_version FROM search_documents "
                "WHERE document_id = ?",
                (document_id,),
            )
            if row is not None and (
                query.conversation_id is None
                or str(row[1]) == str(query.conversation_id)
            ):
                rows.append(row)
        rows.sort(key=lambda row: str(row[2]), reverse=True)
        rows = rows[: query.limit]
        expected_phrase = " ".join(terms)
        results: list[SearchResult] = []
        for row in rows:
            message_id = UUID(str(row[0]))
            conversation_id = UUID(str(row[1]))
            plaintext = await self._encryption.decrypt(
                LocalEncryptionPurpose.SEARCH_INDEX,
                EncryptedLocalValue(int(row[5]), bytes(row[4]), bytes(row[3])),
                self._context(message_id, conversation_id),
            )
            text = plaintext.decode("utf-8")
            if expected_phrase not in " ".join(self._token_service.normalise(text)):
                continue
            results.append(
                SearchResult(
                    message_id,
                    conversation_id,
                    datetime.fromisoformat(str(row[2])),
                    self._excerpt(text, query.text),
                )
            )
        return results

    def _context(self, message_id: UUID, conversation_id: UUID) -> bytes:
        return f"{self._profile_id}:{message_id}:{conversation_id}:search:1".encode(
            "ascii"
        )

    @staticmethod
    def _excerpt(text: str, query: str, maximum: int = 160) -> str:
        folded = unicodedata.normalize("NFKC", text).casefold()
        target = unicodedata.normalize("NFKC", query).casefold()
        index = folded.find(target)
        start = max(0, index - maximum // 3) if index >= 0 else 0
        return text[start : start + maximum]
