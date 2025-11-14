from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.common.dependencies import DependencyComposer, DependencyStack

from ...config import ServerConfig
from ...models.utils import ExtendedAsyncSAEngine
from .database import DatabaseProvider
from .etcd import EtcdProvider
from .redis import CoordinatorValkeyClients, RedisProvider


@dataclass
class InfrastructureResources:
    """All infrastructure resources for app proxy coordinator."""

    db: ExtendedAsyncSAEngine
    valkey: CoordinatorValkeyClients
    traefik_etcd: TraefikEtcd | None


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
        db = await stack.enter_dependency(DatabaseProvider(), setup_input)
        valkey = await stack.enter_dependency(RedisProvider(), setup_input)
        traefik_etcd = await stack.enter_dependency(EtcdProvider(), setup_input)

        yield InfrastructureResources(
            db=db,
            valkey=valkey,
            traefik_etcd=traefik_etcd,
        )
