import logging

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.scheduler.types import ScheduleType
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler

log = BraceStyleAdapter(logging.getLogger(__name__))


class SokovanOrchestrator:
    """
    Orchestrator for Sokovan scheduler.
    Provides event handler interface for the coordinator.
    """

    _coordinator: ScheduleCoordinator

    def __init__(
        self,
        scheduler: Scheduler,
        event_producer: EventProducer,
        valkey_schedule: ValkeyScheduleClient,
    ) -> None:
        self._coordinator = ScheduleCoordinator(
            valkey_schedule=valkey_schedule,
            scheduler=scheduler,
            event_producer=event_producer,
        )

    @property
    def coordinator(self) -> ScheduleCoordinator:
        """Get the schedule coordinator."""
        return self._coordinator

    # Event handlers - delegate to coordinator
    async def handle_schedule_if_needed_event(self, schedule_type: str) -> None:
        """
        Handle conditional scheduling event (checks internal state).
        Called by timer with high frequency (e.g., 5s).
        """
        await self._coordinator.process_if_needed(ScheduleType(schedule_type))

    async def handle_schedule_event(self) -> None:
        """
        Handle unconditional schedule event.
        Called by timer with low frequency (e.g., 30s).
        Direct execution without checking marks.
        """
        handler = self._coordinator._schedule_handlers.get(ScheduleType.SCHEDULE)
        if handler:
            await handler.handle()

    async def handle_check_precond_event(self) -> None:
        """
        Handle unconditional check precondition event.
        Called by timer with low frequency (e.g., 30s).
        """
        handler = self._coordinator._schedule_handlers.get(ScheduleType.CHECK_PRECONDITION)
        if handler:
            await handler.handle()

    async def handle_start_event(self) -> None:
        """
        Handle unconditional session start event.
        Called by timer with low frequency (e.g., 30s).
        """
        handler = self._coordinator._schedule_handlers.get(ScheduleType.START)
        if handler:
            await handler.handle()
