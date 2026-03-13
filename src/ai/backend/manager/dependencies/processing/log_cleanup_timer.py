from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.log.anycast import DoLogCleanupEvent
from ai.backend.manager.defs import LockID
from ai.backend.manager.types import DistributedLockFactory


@dataclass
class LogCleanupTimerInput:
    """Input required for log cleanup timer setup."""

    distributed_lock_factory: DistributedLockFactory
    event_producer: EventProducer


class LogCleanupTimerDependency(
    NonMonitorableDependencyProvider[LogCleanupTimerInput, GlobalTimer]
):
    """Provides GlobalTimer lifecycle for periodic log cleanup.

    Creates a GlobalTimer that periodically fires DoLogCleanupEvent,
    which is consumed by the LogCleanupEventHandler registered in Dispatchers.
    """

    @property
    def stage_name(self) -> str:
        return "log-cleanup-timer"

    @asynccontextmanager
    async def provide(self, setup_input: LogCleanupTimerInput) -> AsyncIterator[GlobalTimer]:
        timer = GlobalTimer(
            setup_input.distributed_lock_factory(LockID.LOCKID_LOG_CLEANUP_TIMER, 20.0),
            setup_input.event_producer,
            lambda: DoLogCleanupEvent(),
            20.0,
            initial_delay=17.0,
            task_name="log_cleanup_task",
        )
        await timer.join()
        try:
            yield timer
        finally:
            await timer.leave()
