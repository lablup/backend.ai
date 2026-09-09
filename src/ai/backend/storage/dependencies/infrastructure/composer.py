from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.configs.redis import RedisConfig
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

from .etcd import EtcdProvider
from .redis import RedisProvider, RedisProviderInput, StorageProxyValkeyClients
from .redis_config import RedisConfigProvider


@dataclass
class InfrastructureComposerInput:
    """Input for Infrastructure composer."""

    local_config: StorageProxyUnifiedConfig
    pidx: int


@dataclass
class InfrastructureResources:
    """All infrastructure resources for storage proxy."""

    etcd: AsyncEtcd
    redis_config: RedisConfig
    valkey: StorageProxyValkeyClients


class InfrastructureComposer(
    DependencyComposer[InfrastructureComposerInput, InfrastructureResources]
):
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
        setup_input: InfrastructureComposerInput,
    ) -> AsyncIterator[InfrastructureResources]:
        """Compose all infrastructure dependencies."""
        local_config = setup_input.local_config

        etcd = await stack.enter_dependency(EtcdProvider(), local_config)
        redis_config = await stack.enter_dependency(RedisConfigProvider(), etcd)
        valkey = await stack.enter_dependency(
            RedisProvider(),
            RedisProviderInput(redis_config=redis_config, pidx=setup_input.pidx),
        )

        yield InfrastructureResources(
            etcd=etcd,
            redis_config=redis_config,
            valkey=valkey,
        )
