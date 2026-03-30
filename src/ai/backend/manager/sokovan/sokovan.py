import logging

from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator

log = BraceStyleAdapter(logging.getLogger(__name__))


class SokovanOrchestrator:
    """
    Orchestrator for Sokovan scheduler.
    Provides event handler interface for the coordinator.
    """

    _deployment_coordinator: DeploymentCoordinator
    _route_coordinator: RouteCoordinator
    _schedule_coordinator: ScheduleCoordinator

    def __init__(
        self,
        schedule_coordinator: ScheduleCoordinator,
        deployment_coordinator: DeploymentCoordinator,
        route_coordinator: RouteCoordinator,
    ) -> None:
        self._schedule_coordinator = schedule_coordinator
        self._deployment_coordinator = deployment_coordinator
        self._route_coordinator = route_coordinator

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
