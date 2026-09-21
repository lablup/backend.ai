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
class ContainerRegistryClients:
    """Container for the clients the container registry domain talks to registries with."""

    quota_pool: ContainerRegistryQuotaClientPool


class ContainerRegistryDependency(DomainDependency[None, ContainerRegistryClients]):
    """Provides the container registry domain's clients."""

    @property
    @override
    def stage_name(self) -> str:
        return "container-registry"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: None) -> AsyncIterator[ContainerRegistryClients]:
        """Initialize and provide the container registry clients.

        Args:
            setup_input: Not used (no dependencies required)

        Yields:
            Initialized ContainerRegistryClients
        """
        yield ContainerRegistryClients(quota_pool=ContainerRegistryQuotaClientPool())
