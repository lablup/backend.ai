from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import override

from ai.backend.manager.clients.container_registry.harbor import (
    ContainerRegistryQuotaClientPool,
)

from .base import DomainDependency


class RegistryQuotaClientPoolDependency(
    DomainDependency[None, ContainerRegistryQuotaClientPool],
):
    """Provides ContainerRegistryQuotaClientPool lifecycle management."""

    @property
    @override
    def stage_name(self) -> str:
        return "registry-quota-client-pool"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: None) -> AsyncIterator[ContainerRegistryQuotaClientPool]:
        """Initialize and provide a registry quota client pool.

        Args:
            setup_input: Not used (no dependencies required)

        Yields:
            Initialized ContainerRegistryQuotaClientPool
        """
        yield ContainerRegistryQuotaClientPool()
