import logging
from collections.abc import Sequence

from ai.backend.common.leader.tasks import EventTaskSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.reconciler.base import ReconcilerTaskSpec
from ai.backend.manager.sokovan.reconciler.coordinator import ReconcilerCoordinator
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
    _reconciler_coordinator: ReconcilerCoordinator
    _reconciler_task_specs: list[ReconcilerTaskSpec]

    def __init__(
        self,
        schedule_coordinator: ScheduleCoordinator,
        deployment_coordinator: DeploymentCoordinator,
        route_coordinator: RouteCoordinator,
        reconciler_coordinator: ReconcilerCoordinator,
        reconciler_task_specs: Sequence[ReconcilerTaskSpec],
    ) -> None:
        self._schedule_coordinator = schedule_coordinator
        self._deployment_coordinator = deployment_coordinator
        self._route_coordinator = route_coordinator
        self._reconciler_coordinator = reconciler_coordinator
        self._reconciler_task_specs = list(reconciler_task_specs)

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

    @property
    def reconciler_coordinator(self) -> ReconcilerCoordinator:
        """Get the reconciler coordinator."""
        return self._reconciler_coordinator

    def create_task_specs(self) -> list[EventTaskSpec]:
        """Create task specifications for leader-based scheduling."""
        specs: list[EventTaskSpec] = []

        # Collect task specs from all coordinators
        specs.extend(self._schedule_coordinator.create_task_specs())
        specs.extend(self._deployment_coordinator.create_task_specs())
        specs.extend(self._route_coordinator.create_task_specs())
        for spec in self._reconciler_task_specs:
            if spec.short_interval is not None:
                specs.append(
                    EventTaskSpec(
                        name=spec.short_task_name,
                        event_factory=spec.create_if_needed_event,
                        interval=spec.short_interval,
                        initial_delay=0.0,
                    )
                )
            specs.append(
                EventTaskSpec(
                    name=spec.long_task_name,
                    event_factory=spec.create_process_event,
                    interval=spec.long_interval,
                    initial_delay=spec.initial_delay,
                )
            )

        return specs
