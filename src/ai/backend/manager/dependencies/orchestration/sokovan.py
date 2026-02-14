from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.http_client.client_pool import (
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.resource_usage_history import (
    ResourceUsageHistoryRepository,
)
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.deployment.coordinator import DeploymentCoordinator
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.coordinator import RouteCoordinator
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.scheduler.coordinator import ScheduleCoordinator
from ai.backend.manager.sokovan.scheduler.factory import (
    CoordinatorHandlersArgs,
    create_coordinator_handlers,
    create_default_scheduler_components,
)
from ai.backend.manager.sokovan.scheduler.fair_share import (
    FairShareAggregator,
    FairShareFactorCalculator,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.sokovan.sokovan import SokovanOrchestrator
from ai.backend.manager.types import DistributedLockFactory

log = BraceStyleAdapter(logging.getLogger(__name__))


@dataclass
class SokovanOrchestratorInput:
    """Input required for sokovan orchestrator setup."""

    # Scheduler component dependencies
    scheduler_repository: SchedulerRepository
    deployment_repository: DeploymentRepository
    fair_share_repository: FairShareRepository
    resource_usage_repository: ResourceUsageHistoryRepository
    config_provider: ManagerConfigProvider
    agent_client_pool: AgentClientPool
    network_plugin_ctx: NetworkPluginContext
    event_producer: EventProducer
    valkey_schedule: ValkeyScheduleClient
    valkey_stat: ValkeyStatClient
    # Controller dependencies
    scheduling_controller: SchedulingController
    deployment_controller: DeploymentController
    route_controller: RouteController
    # Lock factory
    distributed_lock_factory: DistributedLockFactory
    # Service discovery
    service_discovery: ServiceDiscovery


class SokovanOrchestratorDependency(
    NonMonitorableDependencyProvider[SokovanOrchestratorInput, SokovanOrchestrator]
):
    """Provides SokovanOrchestrator lifecycle management.

    Wraps the sokovan orchestrator assembly from the original
    ``sokovan_orchestrator_ctx`` in server.py. Creates scheduler
    components, coordinators, and the orchestrator itself.
    """

    @property
    def stage_name(self) -> str:
        return "sokovan-orchestrator"

    @asynccontextmanager
    async def provide(
        self, setup_input: SokovanOrchestratorInput
    ) -> AsyncIterator[SokovanOrchestrator]:
        """Initialize and provide sokovan orchestrator.

        Args:
            setup_input: Input containing all dependencies for orchestrator assembly

        Yields:
            Configured SokovanOrchestrator
        """
        # Create scheduler components
        scheduler_components = create_default_scheduler_components(
            setup_input.scheduler_repository,
            setup_input.deployment_repository,
            setup_input.fair_share_repository,
            setup_input.config_provider,
            setup_input.agent_client_pool,
            setup_input.network_plugin_ctx,
            setup_input.event_producer,
            setup_input.valkey_schedule,
        )

        # Create HTTP client pool for deployment operations
        client_pool = ClientPool(tcp_client_session_factory)

        # Create deployment coordinator
        deployment_coordinator = DeploymentCoordinator(
            valkey_schedule=setup_input.valkey_schedule,
            deployment_controller=setup_input.deployment_controller,
            deployment_repository=setup_input.deployment_repository,
            event_producer=setup_input.event_producer,
            lock_factory=setup_input.distributed_lock_factory,
            config_provider=setup_input.config_provider,
            scheduling_controller=setup_input.scheduling_controller,
            client_pool=client_pool,
            valkey_stat=setup_input.valkey_stat,
            route_controller=setup_input.route_controller,
        )

        # Create route coordinator
        route_coordinator = RouteCoordinator(
            valkey_schedule=setup_input.valkey_schedule,
            deployment_repository=setup_input.deployment_repository,
            event_producer=setup_input.event_producer,
            lock_factory=setup_input.distributed_lock_factory,
            config_provider=setup_input.config_provider,
            scheduling_controller=setup_input.scheduling_controller,
            client_pool=client_pool,
            service_discovery=setup_input.service_discovery,
        )

        # Create fair share components
        fair_share_aggregator = FairShareAggregator()
        fair_share_calculator = FairShareFactorCalculator()

        # Create coordinator handlers
        coordinator_handlers = create_coordinator_handlers(
            CoordinatorHandlersArgs(
                provisioner=scheduler_components.provisioner,
                launcher=scheduler_components.launcher,
                terminator=scheduler_components.terminator,
                repository=scheduler_components.repository,
                valkey_schedule=setup_input.valkey_schedule,
                scheduling_controller=setup_input.scheduling_controller,
                fair_share_aggregator=fair_share_aggregator,
                fair_share_calculator=fair_share_calculator,
                resource_usage_repository=setup_input.resource_usage_repository,
                fair_share_repository=setup_input.fair_share_repository,
            )
        )

        # Create schedule coordinator
        schedule_coordinator = ScheduleCoordinator(
            valkey_schedule=setup_input.valkey_schedule,
            components=scheduler_components,
            handlers=coordinator_handlers,
            scheduling_controller=setup_input.scheduling_controller,
            event_producer=setup_input.event_producer,
            lock_factory=setup_input.distributed_lock_factory,
        )

        # Create sokovan orchestrator with all coordinators injected
        orchestrator = SokovanOrchestrator(
            schedule_coordinator=schedule_coordinator,
            deployment_coordinator=deployment_coordinator,
            route_coordinator=route_coordinator,
        )

        log.info("Sokovan orchestrator initialized")

        yield orchestrator
