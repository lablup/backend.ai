from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional
from uuid import UUID

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.scheduler_history import (
    SchedulerExecutionHistoryRow,
    SchedulerExecutionStatus,
    SchedulerExecutionStep,
)
from ai.backend.manager.repositories.scheduler_history import SchedulerHistoryRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("SchedulerHistoryService",)


class SchedulerHistoryService:
    """
    Service for managing scheduler execution history.

    Provides high-level APIs for recording scheduler step execution,
    including context manager support for automatic success/failure tracking.
    """

    def __init__(self, db_session: SASession) -> None:
        self._repository = SchedulerHistoryRepository(db_session)
        self._db_session = db_session

    @asynccontextmanager
    async def track_step(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> AsyncIterator[UUID]:
        """
        Context manager for tracking scheduler step execution.

        Automatically records step start, and marks as success or failure
        based on whether an exception is raised.

        Args:
            session_id: ID of the session being processed
            step: The scheduler execution step
            details: Optional metadata about the step execution

        Yields:
            The history record ID

        Example:
            async with history_service.track_step(session_id, SchedulerExecutionStep.SCHEDULE) as history_id:
                # Perform scheduling logic
                pass
            # Automatically marked as SUCCESS if no exception

            async with history_service.track_step(session_id, SchedulerExecutionStep.START) as history_id:
                raise KernelCreationFailed(...)
            # Automatically marked as FAILURE with error info
        """
        history_id = await self._repository.record_step_start(
            session_id, step, details=details
        )

        try:
            yield history_id
            # Mark as success if no exception
            await self._repository.record_step_success(history_id)
        except Exception as e:
            # Mark as failure with error info
            error_info = {
                "type": type(e).__name__,
                "message": str(e),
                "module": type(e).__module__,
            }
            await self._repository.record_step_failure(
                history_id, error_info=error_info
            )
            raise

    async def record_step_start(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> UUID:
        """
        Record the start of a scheduler execution step.

        Use this for manual control when the context manager is not suitable.

        Args:
            session_id: ID of the session being processed
            step: The scheduler execution step
            details: Optional metadata

        Returns:
            The history record ID
        """
        return await self._repository.record_step_start(session_id, step, details=details)

    async def record_step_success(
        self,
        history_id: UUID,
        *,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Mark a scheduler execution step as successful.

        Args:
            history_id: ID of the history record
            details: Optional additional metadata
        """
        await self._repository.record_step_success(history_id, details=details)

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
            history_id: ID of the history record
            error_info: Error information dictionary
            details: Optional additional metadata
        """
        await self._repository.record_step_failure(
            history_id, error_info=error_info, details=details
        )

    async def record_step_retry(
        self,
        session_id: SessionId,
        step: SchedulerExecutionStep,
    ) -> Optional[UUID]:
        """
        Record a retry attempt for a scheduler execution step.

        Increments the retry_count of the latest matching step record instead
        of creating a new record. This merges retry attempts into a single record.

        Args:
            session_id: ID of the session
            step: The scheduler execution step being retried

        Returns:
            The ID of the updated history record, or None if no matching record found
        """
        return await self._repository.record_step_retry(session_id, step)

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
        return await self._repository.get_session_history(session_id)

    async def get_step_summary(
        self,
        session_id: SessionId,
    ) -> dict[str, Any]:
        """
        Get a summary of scheduler execution for a session.

        Args:
            session_id: ID of the session

        Returns:
            Dictionary containing step execution summary with timing and retry info
        """
        history = await self._repository.get_session_history(session_id)

        summary: dict[str, Any] = {
            "session_id": str(session_id),
            "total_steps": len(history),
            "steps": [],
        }

        for record in history:
            step_info = {
                "step": record.step.value if isinstance(record.step, SchedulerExecutionStep) else str(record.step),
                "status": record.status.value if isinstance(record.status, SchedulerExecutionStatus) else str(record.status),
                "started_at": record.started_at.isoformat() if record.started_at else None,
                "finished_at": record.finished_at.isoformat() if record.finished_at else None,
                "retry_count": record.retry_count,
                "duration_seconds": None,
            }

            # Calculate duration if both timestamps are available
            if record.started_at and record.finished_at:
                duration = record.finished_at - record.started_at
                step_info["duration_seconds"] = duration.total_seconds()

            if record.error_info:
                step_info["error_info"] = record.error_info

            if record.details:
                step_info["details"] = record.details

            summary["steps"].append(step_info)

        # Calculate overall statistics
        total_retries = sum(record.retry_count for record in history)
        failed_steps = sum(
            1 for record in history if record.status == SchedulerExecutionStatus.FAILURE
        )
        successful_steps = sum(
            1 for record in history if record.status == SchedulerExecutionStatus.SUCCESS
        )

        summary["statistics"] = {
            "total_retries": total_retries,
            "failed_steps": failed_steps,
            "successful_steps": successful_steps,
            "in_progress_steps": len(history) - failed_steps - successful_steps,
        }

        return summary
