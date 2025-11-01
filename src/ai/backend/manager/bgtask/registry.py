from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.common.bgtask.task.registry import BackgroundTaskHandlerRegistry

from .tasks.purge_images import PurgeImagesHandler
from .tasks.rescan_images import RescanImagesHandler

if TYPE_CHECKING:
    from ai.backend.manager.models.context import GraphQueryContext


class ManagerBgtaskRegistryFactory:
    """
    Factory for creating manager background task handler registry.
    """

    def __init__(self, graph_ctx: GraphQueryContext) -> None:
        self._graph_ctx = graph_ctx

    def create(self) -> BackgroundTaskHandlerRegistry:
        """Create and return a registry with all manager task handlers registered."""
        registry = BackgroundTaskHandlerRegistry()
        registry.register(RescanImagesHandler(self._graph_ctx))
        registry.register(PurgeImagesHandler(self._graph_ctx))

        return registry
