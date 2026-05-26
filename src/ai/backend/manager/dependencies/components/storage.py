from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.models.storage import StorageSessionManager

from .base import ComponentDependency


class StorageManagerDependency(ComponentDependency[StorageSessionManager]):
    """Provides StorageSessionManager lifecycle management."""

    @property
    def stage_name(self) -> str:
        return "storage-manager"

    @asynccontextmanager
    async def provide(
        self, setup_input: ManagerUnifiedConfig
    ) -> AsyncIterator[StorageSessionManager]:
        """Initialize and provide a storage session manager.

        Args:
            setup_input: Configuration containing volume settings

        Yields:
            Initialized StorageSessionManager
        """
        storage_manager = StorageSessionManager(setup_input.volumes)
        try:
            yield storage_manager
        finally:
            await storage_manager.aclose()
