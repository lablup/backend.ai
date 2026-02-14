from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.leader import ValkeyLeaderElection
from ai.backend.common.service_discovery.service_discovery import ServiceDiscovery
from ai.backend.common.types import ValkeyProfileTarget
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.resource_usage_history import (
    ResourceUsageHistoryRepository,
)
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.sokovan.sokovan import SokovanOrchestrator
from ai.backend.manager.types import DistributedLockFactory

from .idle_checker import IdleCheckerHostDependency, IdleCheckerInput
from .leader_election import LeaderElectionDependency, LeaderElectionInput
from .sokovan import SokovanOrchestratorDependency, SokovanOrchestratorInput


@dataclass
class OrchestrationInput:
    """Input required for orchestration layer setup.

    Aggregates all dependencies needed by the orchestration providers
    from lower layers (infrastructure, components, etc.).
    """

    # Common
    db: ExtendedAsyncSAEngine
    config_provider: ManagerConfigProvider
    event_producer: EventProducer
    distributed_lock_factory: DistributedLockFactory
    valkey_profile_target: ValkeyProfileTarget
    valkey_schedule: ValkeyScheduleClient
    valkey_stat: ValkeyStatClient
    pidx: int
    # Sokovan-specific
    scheduler_repository: SchedulerRepository
    deployment_repository: DeploymentRepository
    fair_share_repository: FairShareRepository
    resource_usage_repository: ResourceUsageHistoryRepository
    agent_client_pool: AgentClientPool
    network_plugin_ctx: NetworkPluginContext
    scheduling_controller: SchedulingController
    deployment_controller: DeploymentController
    route_controller: RouteController
    service_discovery: ServiceDiscovery


@dataclass
class OrchestrationResources:
    """Container for all orchestration resources.

    Holds idle checker host, sokovan orchestrator, and leader election.
    """

    idle_checker_host: IdleCheckerHost
    sokovan_orchestrator: SokovanOrchestrator
    leader_election: ValkeyLeaderElection


class OrchestrationComposer(DependencyComposer[OrchestrationInput, OrchestrationResources]):
    """Composes orchestration dependencies at Layer 5.

    Initializes three providers in order:
    1. IdleCheckerHost (independent)
    2. SokovanOrchestrator (independent)
    3. LeaderElection (depends on SokovanOrchestrator for task specs)
    """

    @property
    def stage_name(self) -> str:
        return "orchestration"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: OrchestrationInput,
    ) -> AsyncIterator[OrchestrationResources]:
        """Compose orchestration dependencies in order.

        Args:
            stack: The dependency stack to use for composition
            setup_input: Orchestration input containing all required dependencies

        Yields:
            OrchestrationResources containing idle checker, orchestrator, and election
        """
        # 1. Initialize idle checker host (independent)
        idle_checker_dep = IdleCheckerHostDependency()
        idle_checker_input = IdleCheckerInput(
            db=setup_input.db,
            config_provider=setup_input.config_provider,
            event_producer=setup_input.event_producer,
            lock_factory=setup_input.distributed_lock_factory,
        )
        idle_checker_host = await stack.enter_dependency(
            idle_checker_dep,
            idle_checker_input,
        )

        # 2. Initialize sokovan orchestrator (independent)
        sokovan_dep = SokovanOrchestratorDependency()
        sokovan_input = SokovanOrchestratorInput(
            scheduler_repository=setup_input.scheduler_repository,
            deployment_repository=setup_input.deployment_repository,
            fair_share_repository=setup_input.fair_share_repository,
            resource_usage_repository=setup_input.resource_usage_repository,
            config_provider=setup_input.config_provider,
            agent_client_pool=setup_input.agent_client_pool,
            network_plugin_ctx=setup_input.network_plugin_ctx,
            event_producer=setup_input.event_producer,
            valkey_schedule=setup_input.valkey_schedule,
            valkey_stat=setup_input.valkey_stat,
            scheduling_controller=setup_input.scheduling_controller,
            deployment_controller=setup_input.deployment_controller,
            route_controller=setup_input.route_controller,
            distributed_lock_factory=setup_input.distributed_lock_factory,
            service_discovery=setup_input.service_discovery,
        )
        sokovan_orchestrator = await stack.enter_dependency(
            sokovan_dep,
            sokovan_input,
        )

        # 3. Initialize leader election (depends on sokovan orchestrator)
        leader_dep = LeaderElectionDependency()
        leader_input = LeaderElectionInput(
            valkey_profile_target=setup_input.valkey_profile_target,
            pidx=setup_input.pidx,
            config_provider=setup_input.config_provider,
            event_producer=setup_input.event_producer,
            sokovan_orchestrator=sokovan_orchestrator,
        )
        leader_election = await stack.enter_dependency(
            leader_dep,
            leader_input,
        )

        yield OrchestrationResources(
            idle_checker_host=idle_checker_host,
            sokovan_orchestrator=sokovan_orchestrator,
            leader_election=leader_election,
        )
