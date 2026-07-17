"""Administrative job and background-worker persistence mappings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from bluebubbles.server.database.base import JSON_VALUE_TYPE, Base, UUIDPrimaryKeyMixin
from bluebubbles.server.database.models.announcements import (
    AnnouncementAcknowledgementORM,
    AnnouncementORM,
)

__all__ = [
    "AnnouncementAcknowledgementORM",
    "AnnouncementORM",
    "DataDeletionRequestORM",
    "DataExportJobORM",
    "WorkerExecutionRecordORM",
]


class WorkerExecutionRecordORM(Base, UUIDPrimaryKeyMixin):
    """Map a bounded summary of one background worker execution."""

    __tablename__ = "worker_execution_records"
    __table_args__ = (
        CheckConstraint("processed_count >= 0", name="processed_count_non_negative"),
        CheckConstraint("failure_count >= 0", name="failure_count_non_negative"),
        Index("ix_worker_executions_name_time", "worker_name", "started_at"),
    )

    worker_name: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, object]] = mapped_column(
        JSON_VALUE_TYPE, nullable=False, default=dict
    )


class DataExportJobORM(Base, UUIDPrimaryKeyMixin):
    """Map a controlled export workflow and protected output reference."""

    __tablename__ = "data_export_jobs"
    __table_args__ = (Index("ix_data_export_jobs_status", "status", "created_at"),)

    requested_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    export_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filters: Mapped[dict[str, object]] = mapped_column(
        JSON_VALUE_TYPE, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    storage_reference: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(100))


class DataDeletionRequestORM(Base, UUIDPrimaryKeyMixin):
    """Map an authorised review workflow for user-data deletion."""

    __tablename__ = "data_deletion_requests"
    __table_args__ = (
        Index("ix_data_deletion_requests_status", "status", "requested_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_deletion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_notes: Mapped[str | None] = mapped_column(String(2000))
