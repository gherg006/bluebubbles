"""Authenticated-owner contact request and response contracts."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.models.users import UserSummary


class ContactSummary(ContractModel):
    """Return one contact relationship and its public user summary."""

    id: UUID
    user: UserSummary
    nickname: Annotated[str, Field(max_length=100)] | None = None
    is_favourite: bool = False
    is_blocked: bool = False
    last_contacted: datetime | None = None


class ContactListResponse(ContractModel):
    """Return contacts already sorted by server policy."""

    contacts: tuple[ContactSummary, ...]


class AddContactRequest(ContractModel):
    """Add a contact for the authenticated owner."""

    username: Annotated[str, Field(min_length=1, max_length=128)]


class UpdateContactRequest(ContractModel):
    """Update editable relationship metadata for one contact."""

    nickname: Annotated[str, Field(max_length=100)] | None = None
    is_favourite: bool | None = None


class BlockContactRequest(ContractModel):
    """Set the explicit blocked state for one contact."""

    blocked: bool
