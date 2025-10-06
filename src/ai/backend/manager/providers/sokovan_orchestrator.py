from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@actxmgr
async def sokovan_orchestrator_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ai.backend.common.clients.http_client.client_pool import (
        ClientPool,
        tcp_client_session_factory,
    )

    from ..clients.agent import AgentPool
    from ..sokovan.deployment.coordinator import DeploymentCoordinator
    from ..sokovan.deployment.route.coordinator import RouteCoordinator
    from ..sokovan.scheduler.factory import create_default_scheduler
    from ..sokovan.sokovan import SokovanOrchestrator

    # Create agent pool for scheduler
    agent_pool = AgentPool(root_ctx.agent_cache)

    # Create scheduler with default components
    scheduler = create_default_scheduler(
        root_ctx.repositories.scheduler.repository,
        root_ctx.repositories.deployment.repository,
        root_ctx.config_provider,
        root_ctx.distributed_lock_factory,
        agent_pool,
        root_ctx.network_plugin_ctx,
        root_ctx.event_producer,
        root_ctx.valkey_schedule,
    )

    # Create HTTP client pool for deployment operations
    client_pool = ClientPool(tcp_client_session_factory)

    # Create deployment coordinator
    deployment_coordinator = DeploymentCoordinator(
        valkey_schedule=root_ctx.valkey_schedule,
        deployment_controller=root_ctx.deployment_controller,
        deployment_repository=root_ctx.repositories.deployment.repository,
        event_producer=root_ctx.event_producer,
        lock_factory=root_ctx.distributed_lock_factory,
        config_provider=root_ctx.config_provider,
        scheduling_controller=root_ctx.scheduling_controller,
        client_pool=client_pool,
        valkey_stat=root_ctx.valkey_stat,
        route_controller=root_ctx.route_controller,
    )

    # Create route coordinator
    route_coordinator = RouteCoordinator(
        valkey_schedule=root_ctx.valkey_schedule,
        deployment_repository=root_ctx.repositories.deployment.repository,
        event_producer=root_ctx.event_producer,
        lock_factory=root_ctx.distributed_lock_factory,
        config_provider=root_ctx.config_provider,
        scheduling_controller=root_ctx.scheduling_controller,
        client_pool=client_pool,
    )

    # Create sokovan orchestrator with lock factory for timers
    root_ctx.sokovan_orchestrator = SokovanOrchestrator(
        scheduler=scheduler,
        event_producer=root_ctx.event_producer,
        valkey_schedule=root_ctx.valkey_schedule,
        lock_factory=root_ctx.distributed_lock_factory,
        scheduling_controller=root_ctx.scheduling_controller,
        deployment_coordinator=deployment_coordinator,
        route_coordinator=route_coordinator,
    )

    log.info("Sokovan orchestrator initialized")

    try:
        yield
    finally:
        # Leader election will handle task cleanup
        pass
