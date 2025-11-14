from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack

from ...config import ServerConfig
from .redis import RedisProvider, WorkerValkeyClients


@dataclass
class InfrastructureResources:
    """All infrastructure resources for app proxy worker."""

    valkey: WorkerValkeyClients


class InfrastructureComposer(DependencyComposer[ServerConfig, InfrastructureResources]):
    """Composer for infrastructure layer dependencies."""

    @property
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: ServerConfig,
    ) -> AsyncIterator[InfrastructureResources]:
        """Compose all infrastructure dependencies."""
        # Setup infrastructure in dependency order
        valkey = await stack.enter_dependency(RedisProvider(), setup_input)

        yield InfrastructureResources(
            valkey=valkey,
        )
