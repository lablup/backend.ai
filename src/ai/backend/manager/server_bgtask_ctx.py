from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from .api.context import RootContext


@asynccontextmanager
async def manager_bgtask_registry_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    """
    Initialize manager background task registry.

    The registry is created once at server startup and used throughout
    the server's lifetime. Task handlers are registered with dependencies
    from RootContext.
    """
    from .bgtask.registry import ManagerBgtaskRegistryFactory
    from .models.context import GraphQueryContext
    from .models.gql import DataLoaderManager

    # Create a minimal GraphQueryContext for handler initialization
    # This is only used during setup, not for actual task execution
    graph_ctx = GraphQueryContext(
        schema=None,  # type: ignore[arg-type]  # Not needed for handler initialization
        dataloader_manager=DataLoaderManager(),
        config_provider=root_ctx.config_provider,
        etcd=root_ctx.etcd,
        user={},
        access_key="",
        db=root_ctx.db,
        valkey_stat=root_ctx.valkey_stat,
        valkey_image=root_ctx.valkey_image,
        valkey_live=root_ctx.valkey_live,
        valkey_schedule=root_ctx.valkey_schedule,
        network_plugin_ctx=root_ctx.network_plugin_ctx,
        manager_status=None,  # type: ignore[arg-type]  # Not needed for handler initialization
        known_slot_types={},
        background_task_manager=root_ctx.background_task_manager,
        services_ctx=root_ctx.services_ctx,
        storage_manager=root_ctx.storage_manager,
        registry=root_ctx.registry,
        idle_checker_host=root_ctx.idle_checker_host,
        metric_observer=root_ctx.metrics.gql,
        processors=root_ctx.processors,
    )

    factory = ManagerBgtaskRegistryFactory(graph_ctx)
    root_ctx.manager_bgtask_registry = factory.create()

    yield
