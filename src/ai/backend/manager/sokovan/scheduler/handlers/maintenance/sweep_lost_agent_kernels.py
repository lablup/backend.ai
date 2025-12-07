"""Handler for sweeping kernels with lost agents."""

import logging
from typing import Optional

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

from .base import SchedulerHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class SweepLostAgentKernelsHandler(SchedulerHandler):
    """Handler for sweeping kernels with lost or missing agents."""

    def __init__(
        self,
        scheduler: Scheduler,
        repository: SchedulerRepository,
    ):
        self._scheduler = scheduler
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "sweep-lost-agent-kernels"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Sweep kernels with lost or missing agents."""
        return await self._scheduler.sweep_lost_agent_kernels()

    async def post_process(self, result: ScheduleResult) -> None:
        """Log the number of swept kernels and invalidate cache."""
        log.info("Swept {} sessions with lost agent kernels", len(result.scheduled_sessions))
        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        await self._repository.invalidate_kernel_related_cache(list(affected_keys))
        log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))
