from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.scheduler_history import (
    SchedulerExecutionStep,
)
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.services.scheduler_history import SchedulerHistoryService

from .results import ScheduleResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

__all__ = ("SchedulerHistoryTracker",)


# Mapping from ScheduleType to SchedulerExecutionStep
SCHEDULE_TYPE_TO_STEP: dict[ScheduleType, SchedulerExecutionStep] = {
    ScheduleType.SCHEDULE: SchedulerExecutionStep.SCHEDULE,
    ScheduleType.CHECK_PRECONDITION: SchedulerExecutionStep.CHECK_PRECONDITION,
    ScheduleType.CHECK_PULLING_PROGRESS: SchedulerExecutionStep.CHECK_PULLING_PROGRESS,
    ScheduleType.START: SchedulerExecutionStep.START,
    ScheduleType.CHECK_CREATING_PROGRESS: SchedulerExecutionStep.CHECK_CREATING_PROGRESS,
    ScheduleType.TERMINATE: SchedulerExecutionStep.TERMINATE,
    ScheduleType.CHECK_TERMINATING_PROGRESS: SchedulerExecutionStep.CHECK_TERMINATING_PROGRESS,
    ScheduleType.SWEEP: SchedulerExecutionStep.SWEEP,
}


class SchedulerHistoryTracker:
    """
    Helper class for tracking scheduler execution history.

    Provides methods to record history for scheduler operations based on
    schedule types and execution results.
    """

    def __init__(self, db_session: SASession) -> None:
        self._history_service = SchedulerHistoryService(db_session)
        self._db_session = db_session

    async def track_scheduling_result(
        self,
        schedule_type: ScheduleType,
        result: ScheduleResult,
        *,
        error: Optional[Exception] = None,
    ) -> None:
        """
        Record history for all sessions affected by a scheduling operation.

        For successful operations, records success status for each processed session.
        For failures, records failure status with error information.

        Args:
            schedule_type: Type of scheduling operation
            result: Result of the scheduling operation
            error: Optional exception if the operation failed
        """
        step = SCHEDULE_TYPE_TO_STEP.get(schedule_type)
        if step is None:
            log.warning("Unknown schedule type for history tracking: {}", schedule_type)
            return

        # Get session IDs from result based on schedule type
        session_ids = self._extract_session_ids(schedule_type, result)

        if not session_ids:
            log.debug("No sessions to track for schedule type: {}", schedule_type)
            return

        for session_id in session_ids:
            try:
                if error is not None:
                    # Record failure
                    history_id = await self._history_service.record_step_start(
                        session_id, step
                    )
                    error_info = {
                        "type": type(error).__name__,
                        "message": str(error),
                    }
                    await self._history_service.record_step_failure(
                        history_id, error_info=error_info
                    )
                else:
                    # Record success
                    history_id = await self._history_service.record_step_start(
                        session_id, step
                    )
                    await self._history_service.record_step_success(history_id)
            except Exception as e:
                log.warning(
                    "Failed to record history for session {} step {}: {}",
                    session_id,
                    step,
                    e,
                )

    async def track_retry(
        self,
        schedule_type: ScheduleType,
        session_ids: list[SessionId],
    ) -> None:
        """
        Record retry attempts for sessions.

        Increments retry_count for the latest history record of each session.

        Args:
            schedule_type: Type of scheduling operation being retried
            session_ids: List of session IDs being retried
        """
        step = self._get_retry_step(schedule_type)
        if step is None:
            log.warning("No retry step mapping for schedule type: {}", schedule_type)
            return

        for session_id in session_ids:
            try:
                await self._history_service.record_step_retry(session_id, step)
                log.debug("Recorded retry for session {} step {}", session_id, step)
            except Exception as e:
                log.warning(
                    "Failed to record retry for session {} step {}: {}",
                    session_id,
                    step,
                    e,
                )

    def _extract_session_ids(
        self,
        schedule_type: ScheduleType,
        result: ScheduleResult,
    ) -> list[SessionId]:
        """
        Extract session IDs from scheduling result based on schedule type.

        Args:
            schedule_type: Type of scheduling operation
            result: Result of the scheduling operation

        Returns:
            List of session IDs affected by the operation
        """
        match schedule_type:
            case ScheduleType.SCHEDULE:
                return [s.session_id for s in result.scheduled_sessions]
            case ScheduleType.CHECK_PRECONDITION:
                return [s.session_id for s in result.prepared_sessions]
            case ScheduleType.CHECK_PULLING_PROGRESS:
                return [s.session_id for s in result.ready_sessions]
            case ScheduleType.START:
                return [s.session_id for s in result.started_sessions]
            case ScheduleType.CHECK_CREATING_PROGRESS:
                return [s.session_id for s in result.running_sessions]
            case ScheduleType.TERMINATE:
                return [s.session_id for s in result.terminated_sessions]
            case ScheduleType.CHECK_TERMINATING_PROGRESS:
                return [s.session_id for s in result.cleaned_sessions]
            case ScheduleType.SWEEP:
                return [s.session_id for s in result.swept_sessions]
            case _:
                return []

    def _get_retry_step(
        self,
        schedule_type: ScheduleType,
    ) -> Optional[SchedulerExecutionStep]:
        """
        Get the execution step corresponding to a retry operation.

        Args:
            schedule_type: Type of retry operation

        Returns:
            Corresponding execution step, or None if not a retry type
        """
        match schedule_type:
            case ScheduleType.CHECK_PULLING_PROGRESS:
                return SchedulerExecutionStep.RETRY_PREPARING
            case ScheduleType.CHECK_CREATING_PROGRESS:
                return SchedulerExecutionStep.RETRY_CREATING
            case _:
                return None

    async def get_session_summary(
        self,
        session_id: SessionId,
    ) -> dict[str, Any]:
        """
        Get execution history summary for a session.

        Args:
            session_id: ID of the session

        Returns:
            Dictionary containing execution summary
        """
        return await self._history_service.get_step_summary(session_id)
