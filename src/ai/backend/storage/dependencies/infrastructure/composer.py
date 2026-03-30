from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

from .etcd import EtcdProvider
from .redis import RedisProvider, StorageProxyValkeyClients


@dataclass
class InfrastructureComposerInput:
    """Input for Infrastructure composer."""

    local_config: StorageProxyUnifiedConfig


@dataclass
class InfrastructureResources:
    """All infrastructure resources for storage proxy."""

    etcd: AsyncEtcd
    valkey: StorageProxyValkeyClients


class InfrastructureComposer(
    DependencyComposer[InfrastructureComposerInput, InfrastructureResources]
):
    """Composer for infrastructure layer dependencies."""

    @property
    def stage_name(self) -> str:
        return "infrastructure"

    @asynccontextmanager
    async def compose(
        self,
        stack: DependencyStack,
        setup_input: InfrastructureComposerInput,
    ) -> AsyncIterator[InfrastructureResources]:
        """Compose all infrastructure dependencies."""
        local_config = setup_input.local_config

        # Setup infrastructure in dependency order
        etcd = await stack.enter_dependency(EtcdProvider(), local_config)
        valkey = await stack.enter_dependency(RedisProvider(), etcd)

        yield InfrastructureResources(
            etcd=etcd,
            valkey=valkey,
        )
