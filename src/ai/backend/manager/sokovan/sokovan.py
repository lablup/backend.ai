import logging
from typing import TYPE_CHECKING

import aiotools

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import (
    DoSokovanProcessIfNeededEvent,
    DoSokovanProcessScheduleEvent,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import LockID
from ai.backend.manager.scheduler.dispatcher import SchedulerDispatcher
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

if TYPE_CHECKING:
    from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


class SokovanOrchestrator:
    """
    Orchestrator for Sokovan scheduler.
    Provides event handler interface for the coordinator.
    """

    _coordinator: ScheduleCoordinator
    _event_producer: EventProducer
    _lock_factory: "DistributedLockFactory"
    _scheduler_dispatcher: SchedulerDispatcher  # TODO: Remove this

    # GlobalTimers for scheduling operations
    timers: list[GlobalTimer] = []

    def __init__(
        self,
        scheduler: Scheduler,
        event_producer: EventProducer,
        valkey_schedule: ValkeyScheduleClient,
        lock_factory: "DistributedLockFactory",
        scheduler_dispatcher: SchedulerDispatcher,
    ) -> None:
        self._coordinator = ScheduleCoordinator(
            valkey_schedule=valkey_schedule,
            scheduler=scheduler,
            event_producer=event_producer,
            scheduler_dispatcher=scheduler_dispatcher,
        )
        self._event_producer = event_producer
        self._lock_factory = lock_factory

    @property
    def coordinator(self) -> ScheduleCoordinator:
        """Get the schedule coordinator."""
        return self._coordinator

    async def init_timers(self) -> None:
        """Initialize GlobalTimers for scheduled operations."""
        # Mapping of ScheduleType to LockIDs
        lock_id_map = {
            ScheduleType.SCHEDULE: (
                LockID.LOCKID_SOKOVAN_SCHEDULE_IF_NEEDED_TIMER,
                LockID.LOCKID_SOKOVAN_SCHEDULE_PROCESS_TIMER,
            ),
            ScheduleType.CHECK_PRECONDITION: (
                LockID.LOCKID_SOKOVAN_CHECK_PRECOND_IF_NEEDED_TIMER,
                LockID.LOCKID_SOKOVAN_CHECK_PRECOND_PROCESS_TIMER,
            ),
            ScheduleType.START: (
                LockID.LOCKID_SOKOVAN_START_IF_NEEDED_TIMER,
                LockID.LOCKID_SOKOVAN_START_PROCESS_TIMER,
            ),
            ScheduleType.TERMINATE: (
                LockID.LOCKID_SOKOVAN_TERMINATE_IF_NEEDED_TIMER,
                LockID.LOCKID_SOKOVAN_TERMINATE_PROCESS_TIMER,
            ),
        }

        # Create timers for each ScheduleType
        for schedule_type, (if_needed_lock_id, process_lock_id) in lock_id_map.items():
            # Create closures to capture the schedule_type value
            def create_if_needed_event(
                st: ScheduleType = schedule_type,
            ) -> DoSokovanProcessIfNeededEvent:
                return DoSokovanProcessIfNeededEvent(st.value)

            def create_process_event(
                st: ScheduleType = schedule_type,
            ) -> DoSokovanProcessScheduleEvent:
                return DoSokovanProcessScheduleEvent(st.value)

            # Short cycle timer (5s) - checks marks before execution
            process_if_needed_timer = GlobalTimer(
                self._lock_factory(if_needed_lock_id, 10.0),
                self._event_producer,
                create_if_needed_event,
                interval=5.0,
                task_name=f"sokovan_process_if_needed_{schedule_type.value}",
            )
            self.timers.append(process_if_needed_timer)

            # Long cycle timer (60s) - forced execution
            process_schedule_timer = GlobalTimer(
                self._lock_factory(process_lock_id, 10.0),
                self._event_producer,
                create_process_event,
                interval=60.0,
                initial_delay=30.0,
                task_name=f"sokovan_process_schedule_{schedule_type.value}",
            )
            self.timers.append(process_schedule_timer)

        # Join all timers to start them
        for timer in self.timers:
            await timer.join()

        log.info("Sokovan scheduler timers initialized for all schedule types")

    async def shutdown_timers(self) -> None:
        """Shutdown GlobalTimers gracefully."""
        async with aiotools.TaskGroup() as tg:
            for timer in self.timers:
                tg.create_task(timer.leave())
        log.info("Sokovan scheduler timers stopped")
