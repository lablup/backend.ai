"""Handler for sweeping kernels with stale presence status."""

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


class SweepStaleKernelsHandler(SchedulerHandler):
    """Handler for sweeping kernels with stale presence status.

    This handler checks kernel presence status in Redis and terminates
    kernels that are STALE (no heartbeat from agent for too long).
    Before termination, it confirms with the agent that the kernel
    is truly gone.
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
        return "sweep-stale-kernels"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Sweep kernels with stale presence status."""
        return await self._scheduler.sweep_stale_kernels()

    async def post_process(self, result: ScheduleResult) -> None:
        """Trigger CHECK_RUNNING_SESSION_TERMINATION and invalidate cache if kernels were terminated."""
        log.info("Swept {} stale kernels", len(result.scheduled_sessions))

        # Trigger CHECK_RUNNING_SESSION_TERMINATION to check if sessions need termination
        await self._valkey_schedule_client.mark_schedule_needed(
            ScheduleType.CHECK_RUNNING_SESSION_TERMINATION
        )

        # Invalidate cache for affected access keys
        affected_keys: set[AccessKey] = {
            event_data.access_key for event_data in result.scheduled_sessions
        }
        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug("Invalidated kernel-related cache for {} access keys", len(affected_keys))
