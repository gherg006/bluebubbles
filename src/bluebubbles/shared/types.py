"""Dependency-free identifier aliases used by shared contracts."""

from typing import NewType
from uuid import UUID

UserId = NewType("UserId", UUID)
ConversationId = NewType("ConversationId", UUID)
MessageId = NewType("MessageId", UUID)
AttachmentId = NewType("AttachmentId", UUID)
SessionId = NewType("SessionId", UUID)
CorrelationId = NewType("CorrelationId", UUID)
