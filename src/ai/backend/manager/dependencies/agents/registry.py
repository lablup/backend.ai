from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.sokovan.scheduling_controller.scheduling_controller import (
    SchedulingController,
)


@dataclass
class AgentRegistryInput:
    """Input required for agent registry setup."""

    config_provider: ManagerConfigProvider
    db: ExtendedAsyncSAEngine
    agent_cache: AgentRPCCache
    agent_client_pool: AgentClientPool
    valkey_stat: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_image: ValkeyImageClient
    event_producer: EventProducer
    event_hub: EventHub
    storage_manager: StorageSessionManager
    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext
    scheduling_controller: SchedulingController
    debug: bool
    manager_public_key: PublicKey
    manager_secret_key: SecretKey


class AgentRegistryDependency(
    NonMonitorableDependencyProvider[AgentRegistryInput, AgentRegistry],
):
    """Provides AgentRegistry lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "agent-registry"

    @asynccontextmanager
    async def provide(self, setup_input: AgentRegistryInput) -> AsyncIterator[AgentRegistry]:
        """Initialize and provide an agent registry.

        Creates the AgentRegistry, calls init() for startup,
        and calls shutdown() during cleanup.

        Args:
            setup_input: Input containing all registry dependencies

        Yields:
            Initialized AgentRegistry
        """
        registry = AgentRegistry(
            setup_input.config_provider,
            setup_input.db,
            setup_input.agent_cache,
            setup_input.agent_client_pool,
            setup_input.valkey_stat,
            setup_input.valkey_live,
            setup_input.valkey_image,
            setup_input.event_producer,
            setup_input.event_hub,
            setup_input.storage_manager,
            setup_input.hook_plugin_ctx,
            setup_input.network_plugin_ctx,
            setup_input.scheduling_controller,
            debug=setup_input.debug,
            manager_public_key=setup_input.manager_public_key,
            manager_secret_key=setup_input.manager_secret_key,
        )
        await registry.init()
        try:
            yield registry
        finally:
            await registry.shutdown()
