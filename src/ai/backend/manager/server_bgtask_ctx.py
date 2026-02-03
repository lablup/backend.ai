from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry

from .bgtask.tasks.commit_session import CommitSessionHandler
from .bgtask.tasks.purge_images import PurgeImagesHandler
from .bgtask.tasks.rescan_gpu_alloc_maps import RescanGPUAllocMapsHandler
from .bgtask.tasks.rescan_images import RescanImagesHandler

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
    registry = BackgroundTaskHandlerRegistry()
    registry.register(RescanImagesHandler(root_ctx.processors))
    registry.register(PurgeImagesHandler(root_ctx.processors))

    registry.register(
        RescanGPUAllocMapsHandler(
            agent_repository=root_ctx.repositories.agent.repository,
            agent_client_pool=root_ctx.agent_client_pool,
        )
    )
    registry.register(
        CommitSessionHandler(
            session_repository=root_ctx.repositories.session.repository,
            image_repository=root_ctx.repositories.image.repository,
            agent_registry=root_ctx.registry,
            event_hub=root_ctx.event_hub,
            event_fetcher=root_ctx.event_fetcher,
        )
    )

    root_ctx.background_task_manager.set_registry(registry)

    yield
