import logging
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.scheduler import Scheduler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

if TYPE_CHECKING:
    from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


class SokovanOrchestrator:
    """
    Orchestrator for Sokovan scheduler.
    Provides event handler interface for the coordinator.
    """

    _deployment_coordinator: DeploymentCoordinator
    _route_coordinator: RouteCoordinator
    _schedule_coordinator: ScheduleCoordinator
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
        deployment_coordinator: DeploymentCoordinator,
        route_coordinator: RouteCoordinator,
    ) -> None:
        # Store injected coordinators
        self._deployment_coordinator = deployment_coordinator
        self._route_coordinator = route_coordinator

        # Initialize schedule coordinator
        self._schedule_coordinator = ScheduleCoordinator(
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
        return self._schedule_coordinator

    @property
    def deployment_coordinator(self) -> DeploymentCoordinator:
        """Get the deployment coordinator."""
        return self._deployment_coordinator

    @property
    def route_coordinator(self) -> RouteCoordinator:
        """Get the route coordinator."""
        return self._route_coordinator

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for leader-based scheduling."""
        specs: list[EventTaskSpec] = []

        # Collect task specs from all coordinators
        specs.extend(self._schedule_coordinator.create_task_specs())
        specs.extend(self._deployment_coordinator.create_task_specs())
        specs.extend(self._route_coordinator.create_task_specs())

        return specs
