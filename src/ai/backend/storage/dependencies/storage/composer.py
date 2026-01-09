from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig
from ai.backend.storage.storages.storage_pool import StoragePool

from .storage_pool import StoragePoolProvider


@dataclass
class StorageComposerInput:
    """Input for Storage composer."""

    local_config: StorageProxyUnifiedConfig


@dataclass
class StorageResources:
    """All storage resources for storage proxy."""

    storage_pool: StoragePool


class StorageComposer(DependencyComposer[StorageComposerInput, StorageResources]):
    """Composer for storage layer dependencies."""

    @property
    def stage_name(self) -> str:
        return "storage"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: StorageComposerInput,
    ) -> AsyncIterator[StorageResources]:
        """Compose all storage dependencies."""
        local_config = setup_input.local_config

        # Setup storage
        storage_pool = await stack.enter_dependency(StoragePoolProvider(), local_config)

        yield StorageResources(
            storage_pool=storage_pool,
        )
