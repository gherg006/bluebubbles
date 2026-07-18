"""Thin authenticated HTTP routes for encrypted attachment transfer."""

from __future__ import annotations

import base64
import binascii
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import StreamingResponse

from bluebubbles.server.container import ServerContainer
from bluebubbles.server.dependencies import get_server_container
from bluebubbles.server.domain.sessions import AuthenticatedUser
from bluebubbles.server.routes.authentication import current_authenticated_user
from bluebubbles.server.services.attachments import (
    AttachmentService,
    IncomingEncryptedChunk,
)
from bluebubbles.shared.errors.exceptions import ValidationError
from bluebubbles.shared.models.attachments import (
    AttachmentResponse,
    AuthorisedAttachmentResponse,
    InitialiseUploadRequest,
    InitialiseUploadResponse,
    UploadChunkResponse,
    UploadStatusResponse,
)

router = APIRouter(prefix="/api/v1/attachments", tags=["attachments"])


def _service(container: ServerContainer) -> AttachmentService:
    service = container.services.attachments
    if service is None:
        raise RuntimeError("Attachment service is not configured")
    return service


def _decode_header(value: str, *, expected: int | None = None) -> bytes:
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeError, binascii.Error) as error:
        raise ValidationError(
            user_message="Encrypted chunk headers are invalid."
        ) from error
    if expected is not None and len(decoded) != expected:
        raise ValidationError(user_message="Encrypted chunk headers are invalid.")
    return decoded


@router.post(
    "/uploads",
    response_model=InitialiseUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initialise_upload(
    payload: InitialiseUploadRequest,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> InitialiseUploadResponse:
    return await _service(container).initialise_upload(current, payload)


@router.get("/uploads/{upload_id}", response_model=UploadStatusResponse)
async def upload_status(
    upload_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> UploadStatusResponse:
    return await _service(container).get_upload_status(current, upload_id)


@router.put(
    "/uploads/{upload_id}/chunks/{chunk_index}", response_model=UploadChunkResponse
)
async def upload_chunk(
    upload_id: UUID,
    chunk_index: int,
    request: Request,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
    x_chunk_checksum: Annotated[str, Header()],
    x_chunk_nonce: Annotated[str, Header()],
    x_chunk_authentication_tag: Annotated[str, Header()],
) -> UploadChunkResponse:
    limit = container.settings.attachments.maximum_chunk_size_bytes
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            declared_size = int(declared)
        except ValueError as error:
            raise ValidationError(
                user_message="The encrypted chunk size is invalid."
            ) from error
        if declared_size < 1 or declared_size > limit:
            raise ValidationError(user_message="The encrypted chunk is too large.")
    body = await request.body()
    if not body or len(body) > limit:
        raise ValidationError(user_message="The encrypted chunk size is invalid.")
    return await _service(container).upload_chunk(
        current,
        upload_id,
        chunk_index,
        IncomingEncryptedChunk(
            data=body,
            checksum=_decode_header(x_chunk_checksum, expected=32),
            nonce=_decode_header(x_chunk_nonce, expected=12),
            authentication_tag=_decode_header(x_chunk_authentication_tag, expected=16),
        ),
    )


@router.post("/uploads/{upload_id}/complete", response_model=AttachmentResponse)
async def complete_upload(
    upload_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AttachmentResponse:
    return await _service(container).complete_upload(current, upload_id)


@router.delete("/uploads/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_upload(
    upload_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> Response:
    await _service(container).cancel_upload(current, upload_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{attachment_id}", response_model=AuthorisedAttachmentResponse)
async def get_attachment(
    attachment_id: UUID,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> AuthorisedAttachmentResponse:
    return await _service(container).get_authorised_attachment(current, attachment_id)


@router.get("/{attachment_id}/chunks/{chunk_index}")
async def download_chunk(
    attachment_id: UUID,
    chunk_index: int,
    current: Annotated[AuthenticatedUser, Depends(current_authenticated_user)],
    container: Annotated[ServerContainer, Depends(get_server_container)],
) -> StreamingResponse:
    result = await _service(container).download_chunk(
        current, attachment_id, chunk_index
    )
    return StreamingResponse(
        result.stream,
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(result.metadata.encrypted_size),
            "X-Chunk-Checksum": result.metadata.encrypted_checksum,
            "X-Chunk-Nonce": base64.b64encode(result.metadata.nonce).decode("ascii"),
            "X-Chunk-Authentication-Tag": base64.b64encode(
                result.metadata.authentication_tag
            ).decode("ascii"),
            "X-Chunk-Index": str(chunk_index),
            "X-Total-Chunks": str(result.total_chunks),
        },
    )
