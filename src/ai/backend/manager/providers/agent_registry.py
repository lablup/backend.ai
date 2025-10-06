from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from zmq.auth.certs import load_certificate

from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.manager.sokovan.deployment.deployment_controller import (
    DeploymentController,
    DeploymentControllerArgs,
)
from ai.backend.manager.sokovan.deployment.route.route_controller import (
    RouteController,
    RouteControllerArgs,
)
from ai.backend.manager.sokovan.scheduling_controller import (
    SchedulingController,
    SchedulingControllerArgs,
)

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def agent_registry_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..agent_cache import AgentRPCCache
    from ..registry import AgentRegistry

    # Create scheduling controller first
    root_ctx.scheduling_controller = SchedulingController(
        SchedulingControllerArgs(
            repository=root_ctx.repositories.scheduler.repository,
            config_provider=root_ctx.config_provider,
            storage_manager=root_ctx.storage_manager,
            event_producer=root_ctx.event_producer,
            valkey_schedule=root_ctx.valkey_schedule,
            network_plugin_ctx=root_ctx.network_plugin_ctx,
        )
    )
    # Create deployment controller
    root_ctx.deployment_controller = DeploymentController(
        DeploymentControllerArgs(
            scheduling_controller=root_ctx.scheduling_controller,
            deployment_repository=root_ctx.repositories.deployment.repository,
            config_provider=root_ctx.config_provider,
            storage_manager=root_ctx.storage_manager,
            event_producer=root_ctx.event_producer,
            valkey_schedule=root_ctx.valkey_schedule,
        )
    )
    root_ctx.route_controller = RouteController(
        RouteControllerArgs(
            valkey_schedule=root_ctx.valkey_schedule,
        )
    )
    manager_pkey, manager_skey = load_certificate(
        root_ctx.config_provider.config.manager.rpc_auth_manager_keypair
    )
    assert manager_skey is not None
    manager_public_key = PublicKey(manager_pkey)
    manager_secret_key = SecretKey(manager_skey)
    root_ctx.agent_cache = AgentRPCCache(root_ctx.db, manager_public_key, manager_secret_key)
    root_ctx.registry = AgentRegistry(
        root_ctx.config_provider,
        root_ctx.db,
        root_ctx.agent_cache,
        root_ctx.valkey_stat,
        root_ctx.valkey_live,
        root_ctx.valkey_image,
        root_ctx.event_producer,
        root_ctx.event_hub,
        root_ctx.storage_manager,
        root_ctx.hook_plugin_ctx,
        root_ctx.network_plugin_ctx,
        root_ctx.scheduling_controller,
        debug=root_ctx.config_provider.config.debug.enabled,
        manager_public_key=manager_public_key,
        manager_secret_key=manager_secret_key,
        use_sokovan=root_ctx.config_provider.config.manager.use_sokovan,
    )
    await root_ctx.registry.init()
    yield
    await root_ctx.registry.shutdown()
