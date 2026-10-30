from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.worker.config import ServerConfig
from ai.backend.common.clients.valkey_client.sentinel_monitor.dependency import (
    SentinelMonitorDependency,
)
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.types import RedisProfileTarget

from .redis import RedisProvider, RedisProviderInput, WorkerValkeyClients


@dataclass
class InfrastructureResources:
    """All infrastructure resources for app proxy worker."""

    valkey: WorkerValkeyClients


class InfrastructureComposer(DependencyComposer[ServerConfig, InfrastructureResources]):
    """Composer for infrastructure layer dependencies."""

    @property
    @override
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    @override
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: ServerConfig,
    ) -> AsyncIterator[InfrastructureResources]:
        """Compose all infrastructure dependencies."""
        # Setup infrastructure in dependency order
        sentinel_monitors = await stack.enter_dependency(
            SentinelMonitorDependency(),
            RedisProfileTarget.from_dict(setup_input.redis.to_dict()).valkey_targets(),
        )
        valkey = await stack.enter_dependency(
            RedisProvider(),
            RedisProviderInput(config=setup_input, sentinel_monitors=sentinel_monitors),
        )

        yield InfrastructureResources(
            valkey=valkey,
        )
