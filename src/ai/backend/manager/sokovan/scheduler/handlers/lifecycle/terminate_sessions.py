"""Handler for terminating sessions."""

import logging
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .base import SchedulerHandler

log = BraceStyleAdapter(logging.getLogger(__name__))


class TerminateSessionsHandler(SchedulerHandler):
    """Handler for terminating sessions."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
        repository: SchedulerRepository,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer
        self._repository = repository

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "terminate-sessions"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting TERMINATING sessions."""
        return LockID.LOCKID_SOKOVAN_TARGET_TERMINATING

    async def execute(self) -> ScheduleResult:
        """Terminate sessions marked for termination."""
        return await self._scheduler.terminate_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """
        No post-processing needed.

        Actual status updates and events are handled by:
        - Agent event callbacks (for successful terminations)
        - sweep_lost_agent_kernels() (for lost agents or failed RPC calls)
        """
        # No action needed - terminate_sessions only sends RPC calls
        pass
