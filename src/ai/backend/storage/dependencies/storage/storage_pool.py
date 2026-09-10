from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.storages.storage_pool import StoragePool


@dataclass
class StoragePoolInput:
    """Input required for the storage pool setup."""

    local_config: StorageProxyUnifiedConfig
    pidx: int


class StoragePoolProvider(NonMonitorableDependencyProvider[StoragePoolInput, StoragePool]):
    """Provider for storage pool."""

    @property
    @override
    def stage_name(self) -> str:
        return "storage-pool"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: StoragePoolInput) -> AsyncIterator[StoragePool]:
        """Create and provide storage pool."""
        storage_pool = StoragePool.from_config(setup_input.local_config)
        if setup_input.pidx == 0:
            storage_pool.cleanup_temporary_storages()

        yield storage_pool
