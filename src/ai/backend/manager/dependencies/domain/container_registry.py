from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.manager.clients.container_registry.harbor import (
    ContainerRegistryQuotaClientPool,
)

from .base import DomainDependency


@dataclass
class ContainerRegistryResources:
    """Container for container registry resources."""

    quota_client_pool: ContainerRegistryQuotaClientPool


class ContainerRegistryDependency(DomainDependency[None, ContainerRegistryResources]):
    """Provides the container registry client pool."""

    @property
    @override
    def stage_name(self) -> str:
        return "container-registry"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: None) -> AsyncIterator[ContainerRegistryResources]:
        """Initialize and provide the container registry resources.

        Args:
            setup_input: Not used (no dependencies required)

        Yields:
            Initialized ContainerRegistryResources
        """
        yield ContainerRegistryResources(quota_client_pool=ContainerRegistryQuotaClientPool())
