from __future__ import annotations

from typing import Any

from aiohttp import web

from .app import _mount_registry_tree
from .routing import RouteRegistry


def setup_api(
    root_app: web.Application,
    dep_resources: Any,
    pidx: int,
) -> None:
    """Build the full API module tree and mount it on *root_app*.

    Must be called **after** the Composer has run (so that
    ``dep_resources.processing.processors`` is available) but **before**
    ``runner.setup()`` freezes the application router.
    """
    from .tree import build_api_routes
    from .types import GQLContextDeps

    r = dep_resources
    gql_context_deps = GQLContextDeps(
        config_provider=r.bootstrap.config_provider,
        etcd=r.bootstrap.etcd,
        db=r.infrastructure.db,
        valkey_stat=r.infrastructure.valkey.stat,
        valkey_image=r.infrastructure.valkey.image,
        valkey_live=r.infrastructure.valkey.live,
        valkey_schedule=r.infrastructure.valkey.schedule,
        network_plugin_ctx=r.plugins.network_plugin_ctx,
        background_task_manager=r.system.background_task_manager,
        services_ctx=r.domain.services_ctx,
        storage_manager=r.components.storage_manager,
        registry=r.agents.registry,
        idle_checker_host=r.orchestration.idle_checker_host,
        metric_observer=r.system.metrics.gql,
        processors=r.processing.processors,
        scheduler_repository=r.domain.repositories.scheduler.repository,
        user_repository=r.domain.repositories.user.repository,
        agent_repository=r.domain.repositories.agent.repository,
    )

    root_registry = RouteRegistry.create("", r.system.cors_options)
    for sub in build_api_routes(
        processors=r.processing.processors,
        cors_options=r.system.cors_options,
        config_provider=r.bootstrap.config_provider,
        error_monitor=r.monitoring.error_monitor,
        gql_context_deps=gql_context_deps,
        valkey_rate_limit=r.infrastructure.valkey.rate_limit,
        health_probe=r.system.health_probe,
        root_app=root_app,
        stream_cleanup_handler=r.processing.stream_cleanup_handler,
        pidx=pidx,
    ):
        root_registry.add_subregistry(sub)

    _mount_registry_tree(root_app, root_registry, pidx)

    rlim_reg = root_registry.find_subregistry("ratelimit")
    if rlim_reg is not None and rlim_reg.rlim_middleware is not None:
        root_app.middlewares.append(rlim_reg.rlim_middleware)
