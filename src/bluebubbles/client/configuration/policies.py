"""Server-authoritative policy values consumed by the desktop client."""

from typing import Annotated

from pydantic import Field

from bluebubbles.shared._model import ImmutableContractModel


class ClientPolicy(ImmutableContractModel):
    """Constrain local preferences using authenticated server policy."""

    maximum_attachment_bytes: Annotated[int, Field(gt=0)]
    maximum_cache_bytes: Annotated[int, Field(gt=0)]
    decrypted_cache_allowed: bool
    read_receipts_enabled: bool
    blocked_file_extensions: tuple[str, ...]
    maximum_group_members: Annotated[int, Field(gt=1)]
