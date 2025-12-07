"""Handler for checking RUNNING sessions with all kernels TERMINATED."""

from __future__ import annotations

import logging
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

from ..base import SchedulerHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class CheckRunningSessionTerminationHandler(SchedulerHandler):
    """Handler for checking RUNNING sessions where all kernels are TERMINATED.

    This handler finds RUNNING sessions where all kernels have been terminated
    (e.g., due to agent events or stale kernel sweeping) and marks them as
    TERMINATING so they can proceed to the termination flow.
    """

    def __init__(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ) -> None:
        self._valkey_schedule_client = valkey_schedule_client
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "check-running-session-termination"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Check RUNNING sessions with all kernels TERMINATED and mark as TERMINATING."""
        return await self._scheduler.check_running_session_termination()

    async def post_process(self, result: ScheduleResult) -> None:
        """Trigger CHECK_TERMINATING_PROGRESS and invalidate cache."""
        log.info(
            "{} RUNNING sessions marked as TERMINATING",
            len(result.scheduled_sessions),
        )

        # Trigger CHECK_TERMINATING_PROGRESS to finalize session termination
        await self._valkey_schedule_client.mark_schedule_needed(
            ScheduleType.CHECK_TERMINATING_PROGRESS
        )

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug(
                "Invalidated kernel-related cache for {} access keys",
                len(affected_keys),
            )
