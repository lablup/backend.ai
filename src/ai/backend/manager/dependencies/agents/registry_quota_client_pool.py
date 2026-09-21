from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.common.dependencies import NonMonitorableDependencyProvider
from ai.backend.manager.clients.container_registry.harbor import (
    PerProjectContainerRegistryQuotaClientPool,
)


class RegistryQuotaClientPoolDependency(
    NonMonitorableDependencyProvider[None, PerProjectContainerRegistryQuotaClientPool],
):
    """Provides PerProjectContainerRegistryQuotaClientPool lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "registry-quota-client-pool"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: None
    ) -> AsyncIterator[PerProjectContainerRegistryQuotaClientPool]:
        """Initialize and provide a per-project registry quota client pool.

        Args:
            setup_input: Not used (no dependencies required)

        Yields:
            Initialized PerProjectContainerRegistryQuotaClientPool
        """
        yield PerProjectContainerRegistryQuotaClientPool()
