import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

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
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class SchedulerTimerSpec:
    """Specification and behavior for a scheduler's periodic operation."""

    schedule_type: ScheduleType
    short_lock_id: Optional[LockID]  # None means no short-cycle timer
    long_lock_id: LockID
    short_interval: Optional[float] = 2.0  # None means no short-cycle timer
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> DoSokovanProcessIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoSokovanProcessIfNeededEvent(self.schedule_type.value)

    def create_process_event(self) -> DoSokovanProcessScheduleEvent:
        """Create event for forced processing."""
        return DoSokovanProcessScheduleEvent(self.schedule_type.value)

    @property
    def short_timer_name(self) -> str:
        """Name for the short-cycle timer."""
        return f"sokovan_process_if_needed_{self.schedule_type.value}"

    @property
    def long_timer_name(self) -> str:
        """Name for the long-cycle timer."""
        return f"sokovan_process_schedule_{self.schedule_type.value}"


class SokovanOrchestrator:
    """
    Orchestrator for Sokovan scheduler.
    Provides event handler interface for the coordinator.
    """

    _coordinator: ScheduleCoordinator
    _event_producer: EventProducer
    _lock_factory: "DistributedLockFactory"
    _scheduling_controller: SchedulingController

    # GlobalTimers for scheduling operations
    timers: list[GlobalTimer] = []

    def __init__(
        self,
        scheduler: Scheduler,
        event_producer: EventProducer,
        valkey_schedule: ValkeyScheduleClient,
        lock_factory: "DistributedLockFactory",
        scheduling_controller: SchedulingController,
    ) -> None:
        self._coordinator = ScheduleCoordinator(
            valkey_schedule=valkey_schedule,
            scheduler=scheduler,
            scheduling_controller=scheduling_controller,
            event_producer=event_producer,
            lock_factory=lock_factory,
            config_provider=scheduler._config_provider,
        )
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._scheduling_controller = scheduling_controller

    @property
    def coordinator(self) -> ScheduleCoordinator:
        """Get the schedule coordinator."""
        return self._coordinator

    @staticmethod
    def _create_timer_specs() -> list[SchedulerTimerSpec]:
        """Create timer specifications for all schedule types."""
        return [
            # Regular scheduling operations with both short and long cycle timers
            SchedulerTimerSpec(
                ScheduleType.SCHEDULE,
                LockID.LOCKID_SOKOVAN_SCHEDULE_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_SCHEDULE_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTimerSpec(
                ScheduleType.CHECK_PRECONDITION,
                LockID.LOCKID_SOKOVAN_CHECK_PRECOND_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_CHECK_PRECOND_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTimerSpec(
                ScheduleType.START,
                LockID.LOCKID_SOKOVAN_START_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_START_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTimerSpec(
                ScheduleType.TERMINATE,
                LockID.LOCKID_SOKOVAN_TERMINATE_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_TERMINATE_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Sweep is a maintenance task - only needs long cycle timer
            SchedulerTimerSpec(
                ScheduleType.SWEEP,
                None,  # No short-cycle timer for maintenance tasks
                LockID.LOCKID_SOKOVAN_SWEEP_TIMER,
                short_interval=None,  # No short-cycle timer for maintenance tasks
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Progress check operations with both short and long cycle timers
            SchedulerTimerSpec(
                ScheduleType.CHECK_PULLING_PROGRESS,
                LockID.LOCKID_SOKOVAN_CHECK_PULLING_PROGRESS_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_CHECK_PULLING_PROGRESS_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTimerSpec(
                ScheduleType.CHECK_CREATING_PROGRESS,
                LockID.LOCKID_SOKOVAN_CHECK_CREATING_PROGRESS_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_CHECK_CREATING_PROGRESS_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTimerSpec(
                ScheduleType.CHECK_TERMINATING_PROGRESS,
                LockID.LOCKID_SOKOVAN_CHECK_TERMINATING_PROGRESS_TIMER_SHORT,
                LockID.LOCKID_SOKOVAN_CHECK_TERMINATING_PROGRESS_TIMER_LONG,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Retry operations - only long cycle timers (30 seconds)
            SchedulerTimerSpec(
                ScheduleType.RETRY_PREPARING,
                None,  # No short-cycle timer for retry tasks
                LockID.LOCKID_SOKOVAN_RETRY_PREPARING_TIMER,
                short_interval=None,  # No short-cycle timer
                long_interval=10.0,  # 10 seconds for retry operations
                initial_delay=10.0,  # Wait a bit before first retry
            ),
            SchedulerTimerSpec(
                ScheduleType.RETRY_CREATING,
                None,  # No short-cycle timer for retry tasks
                LockID.LOCKID_SOKOVAN_RETRY_CREATING_TIMER,
                short_interval=None,  # No short-cycle timer
                long_interval=10.0,  # 10 seconds for retry operations
                initial_delay=10.0,  # Wait a bit before first retry
            ),
        ]

    async def init_timers(self) -> None:
        """Initialize GlobalTimers for scheduled operations."""
        timer_specs = self._create_timer_specs()

        # Create timers based on specifications
        for spec in timer_specs:
            if spec.short_interval is not None and spec.short_lock_id is not None:
                # Lock timeout should be slightly longer than interval to prevent overlap
                short_lock_timeout = spec.short_interval * 1.5
                process_if_needed_timer = GlobalTimer(
                    self._lock_factory(spec.short_lock_id, short_lock_timeout),
                    self._event_producer,
                    spec.create_if_needed_event,
                    interval=spec.short_interval,
                    task_name=spec.short_timer_name,
                )
                self.timers.append(process_if_needed_timer)
            # Lock timeout should be slightly longer than interval to prevent overlap
            long_lock_timeout = spec.long_interval * 1.5
            process_schedule_timer = GlobalTimer(
                self._lock_factory(spec.long_lock_id, long_lock_timeout),
                self._event_producer,
                spec.create_process_event,
                interval=spec.long_interval,
                initial_delay=spec.initial_delay,
                task_name=spec.long_timer_name,
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
