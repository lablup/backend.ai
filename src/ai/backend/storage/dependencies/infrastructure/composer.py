from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.dependencies import DependencyComposer, DependencyStack
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.storage.config.unified import StorageProxyUnifiedConfig

from .etcd import EtcdProvider
from .redis import RedisProvider, RedisProviderInput


@dataclass
class InfrastructureComposerInput:
    """Input for Infrastructure composer."""

    local_config: StorageProxyUnifiedConfig


@dataclass
class InfrastructureResources:
    """All infrastructure resources for storage proxy."""

    etcd: AsyncEtcd
    bgtask: ValkeyBgtaskClient
    artifact: ValkeyArtifactDownloadTrackingClient


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
        redis_output = await stack.enter_dependency(
            RedisProvider(),
            RedisProviderInput(local_config=local_config, etcd=etcd),
        )

        yield InfrastructureResources(
            etcd=etcd,
            bgtask=redis_output.bgtask,
            artifact=redis_output.artifact,
        )
