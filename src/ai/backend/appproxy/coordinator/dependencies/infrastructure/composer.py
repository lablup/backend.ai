from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.appproxy.coordinator.models.utils import ExtendedAsyncSAEngine
from ai.backend.common.clients.valkey_client.sentinel_monitor.dependency import (
    SentinelMonitorDependency,
)
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.types import RedisProfileTarget

from .database import DatabaseProvider
from .etcd import EtcdProvider
from .redis import CoordinatorValkeyClients, RedisProvider, RedisProviderInput


@dataclass
class InfrastructureResources:
    """All infrastructure resources for app proxy coordinator."""

    db: ExtendedAsyncSAEngine
    valkey: CoordinatorValkeyClients
    traefik_etcd: TraefikEtcd | None


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
        db = await stack.enter_dependency(DatabaseProvider(), setup_input)
        redis_profile_target = RedisProfileTarget.from_dict(setup_input.redis.to_dict())
        core_redis_profile_target = RedisProfileTarget.from_dict(
            (setup_input.core_redis or setup_input.redis).to_dict()
        )
        sentinel_monitors = await stack.enter_dependency(
            SentinelMonitorDependency(),
            [
                *redis_profile_target.valkey_targets(),
                *core_redis_profile_target.valkey_targets(),
            ],
        )
        valkey = await stack.enter_dependency(
            RedisProvider(),
            RedisProviderInput(config=setup_input, sentinel_monitors=sentinel_monitors),
        )
        traefik_etcd = await stack.enter_dependency(EtcdProvider(), setup_input)

        yield InfrastructureResources(
            db=db,
            valkey=valkey,
            traefik_etcd=traefik_etcd,
        )
