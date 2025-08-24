import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.schedule.anycast import (
    DoSokovanProcessIfNeededEvent,
    DoSokovanProcessScheduleEvent,
)
from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class SchedulerTaskSpec:
    """Specification for a scheduler's periodic task."""

    schedule_type: ScheduleType
    short_interval: Optional[float] = None  # None means no short-cycle task
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> DoSokovanProcessIfNeededEvent:
        """Create event for checking if processing is needed."""
        return DoSokovanProcessIfNeededEvent(self.schedule_type.value)

    def create_process_event(self) -> DoSokovanProcessScheduleEvent:
        """Create event for forced processing."""
        return DoSokovanProcessScheduleEvent(self.schedule_type.value)

    @property
    def short_task_name(self) -> str:
        """Name for the short-cycle task."""
        return f"sokovan_process_if_needed_{self.schedule_type.value}"

    @property
    def long_task_name(self) -> str:
        """Name for the long-cycle task."""
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
    def _create_task_specs() -> list[SchedulerTaskSpec]:
        """Create task specifications for all schedule types."""
        return [
            # Regular scheduling operations with both short and long cycle tasks
            SchedulerTaskSpec(
                ScheduleType.SCHEDULE,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.CHECK_PRECONDITION,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.START,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.TERMINATE,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Sweep is a maintenance task - only needs long cycle task
            SchedulerTaskSpec(
                ScheduleType.SWEEP,
                short_interval=None,  # No short-cycle task for maintenance
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Progress check operations with both short and long cycle tasks
            SchedulerTaskSpec(
                ScheduleType.CHECK_PULLING_PROGRESS,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.CHECK_CREATING_PROGRESS,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            SchedulerTaskSpec(
                ScheduleType.CHECK_TERMINATING_PROGRESS,
                short_interval=2.0,
                long_interval=60.0,
                initial_delay=30.0,
            ),
            # Retry operations - only long cycle tasks
            SchedulerTaskSpec(
                ScheduleType.RETRY_PREPARING,
                short_interval=None,  # No short-cycle task
                long_interval=10.0,  # 10 seconds for retry operations
                initial_delay=10.0,  # Wait a bit before first retry
            ),
            SchedulerTaskSpec(
                ScheduleType.RETRY_CREATING,
                short_interval=None,  # No short-cycle task
                long_interval=10.0,  # 10 seconds for retry operations
                initial_delay=10.0,  # Wait a bit before first retry
            ),
        ]

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for leader-based scheduling."""
        timer_specs = self._create_task_specs()
        specs: list[EventTaskSpec] = []

        for spec in timer_specs:
            # Create short-cycle task spec if specified
            if spec.short_interval is not None:
                short_spec = EventTaskSpec(
                    name=spec.short_task_name,
                    event_factory=spec.create_if_needed_event,
                    interval=spec.short_interval,
                    initial_delay=0.0,  # Start immediately for short tasks
                )
                specs.append(short_spec)

            # Create long-cycle task spec (always present)
            long_spec = EventTaskSpec(
                name=spec.long_task_name,
                event_factory=spec.create_process_event,
                interval=spec.long_interval,
                initial_delay=spec.initial_delay,
            )
            specs.append(long_spec)

        return specs
