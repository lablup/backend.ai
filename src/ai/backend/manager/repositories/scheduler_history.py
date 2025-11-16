from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.scheduler_history import (
    SchedulerExecutionHistoryRow,
    SchedulerExecutionStatus,
    SchedulerExecutionStep,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("SchedulerHistoryRepository",)


class SchedulerHistoryRepository:
    """
    Repository for managing scheduler execution history records.

    Provides methods to record, update, and query scheduler step execution history.
    Supports retry merging by incrementing retry_count instead of creating new records.
    """

    def __init__(self, db_session: SASession) -> None:
        self._db_session = db_session

    async def record_step_start(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> UUID:
        """
        Record the start of a scheduler execution step.

        Args:
            session_id: ID of the session being processed
            step: The scheduler execution step being started
            details: Optional metadata about the step execution

        Returns:
            The ID of the created history record
        """
        history_row = SchedulerExecutionHistoryRow(
            session_id=session_id,
            step=step,
            status=SchedulerExecutionStatus.IN_PROGRESS,
            details=details,
        )
        self._db_session.add(history_row)
        await self._db_session.flush()
        return history_row.id

    async def record_step_success(
        self,
        history_id: UUID,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Mark a scheduler execution step as successful.

        Args:
            history_id: ID of the history record to update
            details: Optional additional metadata to merge with existing details
        """
        now = datetime.now().astimezone()
        update_values: dict[str, Any] = {
            "status": SchedulerExecutionStatus.SUCCESS,
            "finished_at": now,
        }

        if details is not None:
            # Merge new details with existing details
            update_values["details"] = sa.func.coalesce(
                sa.func.jsonb_concat(
                    SchedulerExecutionHistoryRow.details,
                    sa.cast(details, pgsql.JSONB),
                ),
                sa.cast(details, pgsql.JSONB),
            )

        stmt = (
            sa.update(SchedulerExecutionHistoryRow)
            .where(SchedulerExecutionHistoryRow.id == history_id)
            .values(**update_values)
        )
        await self._db_session.execute(stmt)

    async def record_step_failure(
        self,
        history_id: UUID,
        *,
        error_info: Optional[dict[str, Any]] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Mark a scheduler execution step as failed.

        Args:
            history_id: ID of the history record to update
            error_info: Error information dictionary
            details: Optional additional metadata to merge with existing details
        """
        now = datetime.now().astimezone()
        update_values: dict[str, Any] = {
            "status": SchedulerExecutionStatus.FAILURE,
            "finished_at": now,
        }

        if error_info is not None:
            update_values["error_info"] = error_info

        if details is not None:
            update_values["details"] = sa.func.coalesce(
                sa.func.jsonb_concat(
                    SchedulerExecutionHistoryRow.details,
                    sa.cast(details, pgsql.JSONB),
                ),
                sa.cast(details, pgsql.JSONB),
            )

        stmt = (
            sa.update(SchedulerExecutionHistoryRow)
            .where(SchedulerExecutionHistoryRow.id == history_id)
            .values(**update_values)
        )
        await self._db_session.execute(stmt)

    async def record_step_retry(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
    ) -> Optional[UUID]:
        """
        Record a retry attempt for a scheduler execution step.
        Increments the retry_count of the latest matching step record.

        Args:
            session_id: ID of the session
            step: The scheduler execution step being retried

        Returns:
            The ID of the updated history record, or None if no matching record found
        """
        # Find the latest history record for this session and step
        latest_query = (
            sa.select(SchedulerExecutionHistoryRow)
            .where(
                SchedulerExecutionHistoryRow.session_id == session_id,
                SchedulerExecutionHistoryRow.step == step,
            )
            .order_by(SchedulerExecutionHistoryRow.started_at.desc())
            .limit(1)
        )
        result = await self._db_session.execute(latest_query)
        latest_row = result.scalar_one_or_none()

        if latest_row is None:
            log.warning(
                "No history record found for session {} step {} during retry",
                session_id,
                step,
            )
            return None

        # Update retry count and timestamp
        now = datetime.now().astimezone()
        stmt = (
            sa.update(SchedulerExecutionHistoryRow)
            .where(SchedulerExecutionHistoryRow.id == latest_row.id)
            .values(
                retry_count=SchedulerExecutionHistoryRow.retry_count + 1,
                last_retry_at=now,
                status=SchedulerExecutionStatus.IN_PROGRESS,
                finished_at=None,  # Reset finished_at for retry
            )
        )
        await self._db_session.execute(stmt)
        return latest_row.id

    async def get_session_history(
        self,
        session_id: SessionId,
    ) -> list[SchedulerExecutionHistoryRow]:
        """
        Retrieve the complete execution history for a session.

        Args:
            session_id: ID of the session

        Returns:
            List of history records ordered by started_at
        """
        stmt = (
            sa.select(SchedulerExecutionHistoryRow)
            .where(SchedulerExecutionHistoryRow.session_id == session_id)
            .order_by(SchedulerExecutionHistoryRow.started_at.asc())
        )
        result = await self._db_session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_step_history(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
    ) -> Optional[SchedulerExecutionHistoryRow]:
        """
        Get the latest history record for a specific session and step.

        Args:
            session_id: ID of the session
            step: The scheduler execution step

        Returns:
            The latest history record for the step, or None if not found
        """
        stmt = (
            sa.select(SchedulerExecutionHistoryRow)
            .where(
                SchedulerExecutionHistoryRow.session_id == session_id,
                SchedulerExecutionHistoryRow.step == step,
            )
            .order_by(SchedulerExecutionHistoryRow.started_at.desc())
            .limit(1)
        )
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_in_progress_steps(
        self,
        session_id: SessionId,
    ) -> list[SchedulerExecutionHistoryRow]:
        """
        Get all in-progress step records for a session.

        Args:
            session_id: ID of the session

        Returns:
            List of in-progress history records
        """
        stmt = (
            sa.select(SchedulerExecutionHistoryRow)
            .where(
                SchedulerExecutionHistoryRow.session_id == session_id,
                SchedulerExecutionHistoryRow.status == SchedulerExecutionStatus.IN_PROGRESS,
            )
            .order_by(SchedulerExecutionHistoryRow.started_at.asc())
        )
        result = await self._db_session.execute(stmt)
        return list(result.scalars().all())
