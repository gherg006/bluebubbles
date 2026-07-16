"""Client-visible attachment metadata, separate from plaintext file bytes."""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ClientAttachment:
    """Describe an authorised attachment and optional local encrypted location."""

    id: UUID
    conversation_id: UUID
    display_filename: str
    media_type: str
    encrypted_size: int
    encrypted_local_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.display_filename or not self.media_type or self.encrypted_size <= 0:
            raise ValueError("Attachment metadata is incomplete")
