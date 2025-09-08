"""Handler for retrying preparing sessions."""

import logging
from typing import Optional

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.scheduler.results import ScheduleResult
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

from .base import SchedulerHandler

log = BraceStyleAdapter(logging.getLogger(__name__))

# Time thresholds for health checks
PREPARING_CHECK_THRESHOLD = 900.0  # 15 minutes


class RetryPreparingHandler(SchedulerHandler):
    """Handler for retrying PREPARING/PULLING sessions that appear stuck."""

    def __init__(
        self,
        scheduler: Scheduler,
        scheduling_controller: SchedulingController,
        event_producer: EventProducer,
    ):
        self._scheduler = scheduler
        self._scheduling_controller = scheduling_controller
        self._event_producer = event_producer

    @classmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        return "retry-preparing"

    @property
    def lock_id(self) -> Optional[LockID]:
        """Lock for operations targeting PREPARING sessions (retry)."""
        return LockID.LOCKID_SOKOVAN_TARGET_PREPARING

    async def execute(self) -> ScheduleResult:
        """Check and retry stuck PREPARING/PULLING sessions."""
        log.debug("Checking for stuck PREPARING/PULLING sessions to retry")

        # Call scheduler method to handle retry logic
        return await self._scheduler.retry_preparing_sessions()

    async def post_process(self, result: ScheduleResult) -> None:
        """Request precondition check if sessions were retried."""
        log.info("Retried {} stuck PREPARING/PULLING sessions", len(result.scheduled_sessions))
