from __future__ import annotations

from dataclasses import dataclass

from zmq.auth.certs import load_certificate

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.setup.infrastructure.redis import ValkeyClients
from ai.backend.manager.setup.messaging.event_producer import EventProducerResource


@dataclass
class AgentRegistrySpec:
    config_provider: ManagerConfigProvider
    database: ExtendedAsyncSAEngine
    valkey_clients: ValkeyClients
    event_producer_resource: EventProducerResource
    storage_manager: StorageSessionManager
    hook_plugin_ctx: HookPluginContext
    network_plugin_ctx: NetworkPluginContext


@dataclass
class AgentRegistryResource:
    agent_cache: AgentRPCCache
    registry: AgentRegistry


class AgentRegistryProvisioner(Provisioner[AgentRegistrySpec, AgentRegistryResource]):
    @property
    def name(self) -> str:
        return "agent_registry"

    async def setup(self, spec: AgentRegistrySpec) -> AgentRegistryResource:
        manager_pkey, manager_skey = load_certificate(
            spec.config_provider.config.manager.rpc_auth_manager_keypair
        )
        assert manager_skey is not None
        manager_public_key = PublicKey(manager_pkey)
        manager_secret_key = SecretKey(manager_skey)
        
        agent_cache = AgentRPCCache(spec.database, manager_public_key, manager_secret_key)
        
        registry = AgentRegistry(
            spec.config_provider,
            spec.database,
            agent_cache,
            spec.valkey_clients.valkey_stat,
            spec.valkey_clients.valkey_live,
            spec.valkey_clients.valkey_image,
            spec.event_producer_resource.event_producer,
            spec.storage_manager,
            spec.hook_plugin_ctx,
            spec.network_plugin_ctx,
            debug=spec.config_provider.config.debug.enabled,
            manager_public_key=manager_public_key,
            manager_secret_key=manager_secret_key,
        )
        await registry.init()
        
        return AgentRegistryResource(
            agent_cache=agent_cache,
            registry=registry,
        )

    async def teardown(self, resource: AgentRegistryResource) -> None:
        await resource.registry.shutdown()