from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.deployment.deployment_controller import DeploymentController
from ai.backend.manager.sokovan.deployment.revision_draft import RevisionDraftReader
from ai.backend.manager.sokovan.deployment.route.route_controller import RouteController
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment_revision_preset.repository import (
        DeploymentRevisionPresetRepository,
    )

from .agent_client_pool import AgentClientPoolDependency, AgentClientPoolInput
from .appproxy_client_pool import AppProxyClientPoolDependency
from .deployment_controller import DeploymentControllerDependency, DeploymentControllerInput
from .registry import AgentRegistryDependency, AgentRegistryInput
from .route_controller import RouteControllerDependency, RouteControllerInput
from .scheduling_controller import SchedulingControllerDependency, SchedulingControllerInput


@dataclass
class AgentsInput:
    """Input required for agents layer setup.

    Contains configuration, infrastructure, and component resources
    from previous dependency stages.
    """

    config: ManagerUnifiedConfig
    config_provider: ManagerConfigProvider
    db: ExtendedAsyncSAEngine
    valkey_clients: ValkeyClients
    storage_manager: StorageSessionManager
    agent_cache: AgentRPCCache
    event_producer: EventProducer
    event_hub: EventHub
    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext
    scheduler_repository: SchedulerRepository
    deployment_repository: DeploymentRepository
    deployment_revision_preset_repository: DeploymentRevisionPresetRepository | None
    runtime_variant_repository: RuntimeVariantRepository


@dataclass
class AgentsResources:
    """Container for all agent-layer resources.

    Holds controllers, client pools, and registry.
    """

    scheduling_controller: SchedulingController
    revision_draft_reader: RevisionDraftReader
    deployment_controller: DeploymentController
    route_controller: RouteController
    agent_client_pool: AgentClientPool
    appproxy_client_pool: AppProxyClientPool
    registry: AgentRegistry


class AgentsComposer(DependencyComposer[AgentsInput, AgentsResources]):
    """Composes all agent-layer dependencies (Layer 4)."""

    @property
    @override
    def stage_name(self) -> str:
        return "agents"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: AgentsInput,
    ) -> AsyncIterator[AgentsResources]:
        valkey_schedule = setup_input.valkey_clients.schedule

        # 1. Scheduling controller
        scheduling_controller = await stack.enter_dependency(
            SchedulingControllerDependency(),
            SchedulingControllerInput(
                repository=setup_input.scheduler_repository,
                config_provider=setup_input.config_provider,
                storage_manager=setup_input.storage_manager,
                event_producer=setup_input.event_producer,
                valkey_schedule=valkey_schedule,
                network_plugin_ctx=setup_input.network_plugin_ctx,
                hook_plugin_ctx=setup_input.hook_plugin_ctx,
            ),
        )

        # 2. Revision draft reader (read-side of the revision merge pipeline)
        revision_draft_reader = RevisionDraftReader(
            deployment_repository=setup_input.deployment_repository,
        )

        # 3. Deployment controller
        deployment_controller = await stack.enter_dependency(
            DeploymentControllerDependency(),
            DeploymentControllerInput(
                scheduling_controller=scheduling_controller,
                deployment_repository=setup_input.deployment_repository,
                config_provider=setup_input.config_provider,
                storage_manager=setup_input.storage_manager,
                event_producer=setup_input.event_producer,
                valkey_schedule=valkey_schedule,
                revision_draft_reader=revision_draft_reader,
                deployment_revision_preset_repository=setup_input.deployment_revision_preset_repository,
            ),
        )

        # 4. Route controller
        route_controller = await stack.enter_dependency(
            RouteControllerDependency(),
            RouteControllerInput(
                valkey_schedule=valkey_schedule,
            ),
        )

        # 5. Agent client pool
        agent_client_pool = await stack.enter_dependency(
            AgentClientPoolDependency(),
            AgentClientPoolInput(
                agent_cache=setup_input.agent_cache,
            ),
        )

        # 6. App proxy client pool
        appproxy_client_pool = await stack.enter_dependency(
            AppProxyClientPoolDependency(),
            None,
        )

        # 7. Agent registry
        registry = await stack.enter_dependency(
            AgentRegistryDependency(),
            AgentRegistryInput(
                config_provider=setup_input.config_provider,
                db=setup_input.db,
                agent_cache=setup_input.agent_cache,
                agent_client_pool=agent_client_pool,
                valkey_stat=setup_input.valkey_clients.stat,
                valkey_live=setup_input.valkey_clients.live,
                valkey_image=setup_input.valkey_clients.image,
                event_producer=setup_input.event_producer,
                event_hub=setup_input.event_hub,
                storage_manager=setup_input.storage_manager,
                hook_plugin_ctx=setup_input.hook_plugin_ctx,
                network_plugin_ctx=setup_input.network_plugin_ctx,
                scheduling_controller=scheduling_controller,
                scheduler_repository=setup_input.scheduler_repository,
                debug=setup_input.config_provider.config.debug.enabled,
                manager_public_key=setup_input.agent_cache.manager_public_key,
                manager_secret_key=setup_input.agent_cache.manager_secret_key,
            ),
        )

        yield AgentsResources(
            scheduling_controller=scheduling_controller,
            revision_draft_reader=revision_draft_reader,
            deployment_controller=deployment_controller,
            route_controller=route_controller,
            agent_client_pool=agent_client_pool,
            appproxy_client_pool=appproxy_client_pool,
            registry=registry,
        )
