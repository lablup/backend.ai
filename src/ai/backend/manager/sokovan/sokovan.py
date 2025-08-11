import logging

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.logging import BraceStyleAdapter
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
