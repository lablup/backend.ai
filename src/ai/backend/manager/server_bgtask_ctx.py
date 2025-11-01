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
    from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry

    from .bgtask.tasks.purge_images import PurgeImagesHandler
    from .bgtask.tasks.rescan_images import RescanImagesHandler

    registry = BackgroundTaskHandlerRegistry()
    registry.register(RescanImagesHandler(root_ctx.processors))
    registry.register(PurgeImagesHandler(root_ctx.processors))

    root_ctx.manager_bgtask_registry = registry

    yield
