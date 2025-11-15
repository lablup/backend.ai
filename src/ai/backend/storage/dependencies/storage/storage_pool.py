from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.storages.storage_pool import StoragePool


class StoragePoolProvider(NonMonitorableDependencyProvider[StorageProxyUnifiedConfig, StoragePool]):
    """Provider for storage pool."""

    @property
    def stage_name(self) -> str:
        return "storage-pool"

    @asynccontextmanager
    async def provide(self, setup_input: StorageProxyUnifiedConfig) -> AsyncIterator[StoragePool]:
        """Create and provide storage pool."""
        storage_pool = StoragePool.from_config(setup_input)

        # StoragePool doesn't have explicit cleanup, but yield it as a context manager
        yield storage_pool
