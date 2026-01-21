"""Post-processor for marking next schedule type."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.scheduler.types import ScheduleType

from .base import PostProcessor, PostProcessorContext

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

log = BraceStyleAdapter(logging.getLogger(__name__))


# Mapping from target session status to next schedule type.
# After a session transitions to a status, the coordinator marks the corresponding
# schedule type to trigger the next phase.
STATUS_TO_NEXT_SCHEDULE_TYPE: dict[SessionStatus, ScheduleType] = {
    SessionStatus.PENDING: ScheduleType.SCHEDULE,
    SessionStatus.SCHEDULED: ScheduleType.CHECK_PRECONDITION,
    SessionStatus.PREPARED: ScheduleType.START,
    SessionStatus.DEPRIORITIZING: ScheduleType.DEPRIORITIZE,
    SessionStatus.TERMINATING: ScheduleType.TERMINATE,
}


class ScheduleMarkingPostProcessor(PostProcessor):
    """Post-processor that marks the next schedule type based on target statuses."""

    def __init__(self, scheduling_controller: SchedulingController) -> None:
        self._scheduling_controller = scheduling_controller

    async def execute(self, context: PostProcessorContext) -> None:
        """Mark the next schedule types for all target statuses."""
        if not context.target_statuses:
            return

        # Collect unique schedule types to mark (deduplicate since multiple statuses
        # might map to the same schedule type)
        schedule_types_to_mark: set[ScheduleType] = set()
        for target_status in context.target_statuses:
            next_schedule_type = STATUS_TO_NEXT_SCHEDULE_TYPE.get(target_status)
            if next_schedule_type is not None:
                schedule_types_to_mark.add(next_schedule_type)

        if not schedule_types_to_mark:
            return

        # Mark all schedule types in batch
        await self._scheduling_controller.mark_scheduling_needed(list(schedule_types_to_mark))
        log.debug(
            "Marked {} schedule type(s) for status transitions to {}",
            len(schedule_types_to_mark),
            context.target_statuses,
        )
