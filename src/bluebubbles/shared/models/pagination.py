"""Opaque cursor and bounded page request/response contracts."""

from typing import Annotated, Generic, TypeVar

from pydantic import Field, RootModel

from bluebubbles.shared._model import ContractModel
from bluebubbles.shared.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

T = TypeVar("T")


class OpaqueCursor(RootModel[str]):
    """Hold an opaque cursor without interpreting or generating it."""

    root: Annotated[str, Field(min_length=1, max_length=2048)]


class PageRequest(ContractModel):
    """Request a bounded cursor page in one direction."""

    limit: Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE
    before: OpaqueCursor | None = None
    after: OpaqueCursor | None = None

    def model_post_init(self, context: object) -> None:
        """Reject ambiguous bidirectional cursor requests."""
        if self.before is not None and self.after is not None:
            raise ValueError("Only one of before or after may be supplied")


class CursorPageMetadata(ContractModel):
    """Describe navigation around a returned cursor page."""

    next_cursor: OpaqueCursor | None = None
    previous_cursor: OpaqueCursor | None = None
    has_more: bool = False


class CursorPage(ContractModel, Generic[T]):  # noqa: UP046 - Python 3.12 test runtime
    """Return typed items together with opaque cursor metadata."""

    items: tuple[T, ...]
    page: CursorPageMetadata
