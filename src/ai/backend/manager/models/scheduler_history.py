from __future__ import annotations

import enum
import logging
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.orm import relationship

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter

from .base import (
    Base,
    IDColumn,
    SessionIDColumnType,
    StrEnumType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = (
    "SchedulerExecutionStep",
    "SchedulerExecutionStatus",
    "SchedulerExecutionHistoryRow",
)


class SchedulerExecutionStep(enum.StrEnum):
    """
    Represents the discrete steps/phases in the scheduler execution flow.
    """

    # Main scheduling phases
    SCHEDULE = "SCHEDULE"  # PENDING -> SCHEDULED
    CHECK_PRECONDITION = "CHECK_PRECONDITION"  # SCHEDULED -> PREPARING
    CHECK_PULLING_PROGRESS = "CHECK_PULLING_PROGRESS"  # PREPARING/PULLING -> PREPARED
    START = "START"  # PREPARED -> CREATING
    CHECK_CREATING_PROGRESS = "CHECK_CREATING_PROGRESS"  # CREATING -> RUNNING
    TERMINATE = "TERMINATE"  # Any -> TERMINATING
    CHECK_TERMINATING_PROGRESS = "CHECK_TERMINATING_PROGRESS"  # TERMINATING -> TERMINATED
    SWEEP = "SWEEP"  # Maintenance: Clean up stale PENDING sessions

    # Retry operations
    RETRY_PREPARING = "RETRY_PREPARING"  # Retry stuck image pulls
    RETRY_CREATING = "RETRY_CREATING"  # Retry stuck kernel creation


class SchedulerExecutionStatus(enum.StrEnum):
    """
    Status of a scheduler execution step.
    """

    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class SchedulerExecutionHistoryRow(Base):
    """
    Records the execution history of scheduler steps for each session.
    Multiple retries of the same step are merged by incrementing retry_count.
    """

    __tablename__ = "scheduler_execution_history"

    id = IDColumn("id")

    session_id = sa.Column(
        "session_id",
        SessionIDColumnType,
        sa.ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Step information
    step = sa.Column(
        "step",
        StrEnumType(SchedulerExecutionStep),
        nullable=False,
        index=True,
    )
    started_at = sa.Column(
        "started_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    finished_at = sa.Column(
        "finished_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Retry merging
    retry_count = sa.Column(
        "retry_count",
        sa.Integer,
        default=0,
        nullable=False,
    )
    last_retry_at = sa.Column(
        "last_retry_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Result status
    status = sa.Column(
        "status",
        StrEnumType(SchedulerExecutionStatus),
        nullable=False,
        default=SchedulerExecutionStatus.IN_PROGRESS,
    )

    # Error information (when status is FAILURE)
    error_info = sa.Column(
        "error_info",
        pgsql.JSONB,
        nullable=True,
        default=None,
    )

    # Additional metadata (e.g., selected agent, allocated resources, etc.)
    details = sa.Column(
        "details",
        pgsql.JSONB,
        nullable=True,
        default=None,
    )

    # Relationship
    session = relationship("SessionRow", back_populates="scheduler_history")

    __table_args__ = (
        # Index for efficient queries on session + step + status
        sa.Index(
            "ix_scheduler_execution_history_session_step",
            "session_id",
            "step",
            "started_at",
        ),
    )

    def __init__(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
        status: SchedulerExecutionStatus = SchedulerExecutionStatus.IN_PROGRESS,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        retry_count: int = 0,
        last_retry_at: Optional[datetime] = None,
        error_info: Optional[dict[str, Any]] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.session_id = session_id
        self.step = step
        self.status = status
        if started_at is not None:
            self.started_at = started_at
        self.finished_at = finished_at
        self.retry_count = retry_count
        self.last_retry_at = last_retry_at
        self.error_info = error_info
        self.details = details

    def __repr__(self) -> str:
        return (
            f"SchedulerExecutionHistoryRow("
            f"id={self.id}, "
            f"session_id={self.session_id}, "
            f"step={self.step}, "
            f"status={self.status}, "
            f"retry_count={self.retry_count})"
        )
