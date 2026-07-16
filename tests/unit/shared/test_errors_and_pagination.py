"""Tests for stable errors and bounded opaque pagination."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from bluebubbles.shared.errors import (
    ERROR_METADATA,
    ApiErrorDetail,
    ApiErrorResponse,
    ErrorCode,
    RetryClassification,
    get_error_metadata,
)
from bluebubbles.shared.models.pagination import (
    CursorPage,
    CursorPageMetadata,
    OpaqueCursor,
    PageRequest,
)


def test_every_error_code_has_stable_metadata() -> None:
    assert set(ERROR_METADATA) == set(ErrorCode)
    assert get_error_metadata(ErrorCode.INVALID_TOKEN).http_status == 401
    assert get_error_metadata(ErrorCode.USER_NOT_FOUND).http_status == 404
    assert get_error_metadata(ErrorCode.CONFLICT).http_status == 409
    assert (
        get_error_metadata(ErrorCode.RATE_LIMIT_EXCEEDED).retry
        is RetryClassification.RETRY_AFTER
    )
    assert get_error_metadata(ErrorCode.INTERNAL_ERROR).http_status == 500


def test_api_error_serialises_only_explicit_safe_fields() -> None:
    response = ApiErrorResponse(
        error=ApiErrorDetail(
            code=ErrorCode.INVALID_LOGIN,
            message="Login failed",
            retryable=False,
        ),
        correlation_id=uuid4(),
    )
    assert response.model_dump()["success"] is False
    with pytest.raises(ValidationError, match="Extra inputs"):
        ApiErrorResponse.model_validate(
            {
                "error": {
                    "code": "INVALID_LOGIN",
                    "message": "Login failed",
                    "retryable": False,
                },
                "correlation_id": str(uuid4()),
                "technical_exception": "LDAP stack trace",
            }
        )


def test_page_request_is_bounded_and_unambiguous() -> None:
    assert PageRequest().limit == 50
    with pytest.raises(ValidationError):
        PageRequest(limit=251)
    with pytest.raises(ValidationError, match="Only one"):
        PageRequest(before=OpaqueCursor("before"), after=OpaqueCursor("after"))


def test_generic_cursor_page_preserves_typed_items() -> None:
    page = CursorPage[int](
        items=(1, 2),
        page=CursorPageMetadata(next_cursor=OpaqueCursor("next"), has_more=True),
    )
    assert page.items == (1, 2)
    assert page.page.next_cursor == OpaqueCursor("next")
