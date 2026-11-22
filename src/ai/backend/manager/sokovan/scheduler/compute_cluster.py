"""Which compute cluster a session runs in, for the launcher and the terminator.

A resource group whose driver is `kubernetes` names its cluster in `driver_opts.compute_cluster`;
the cluster's only agent is its session gateway.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Collection, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime

from ai.backend.common.dto.manager.v2.resource_group.request import (
    DEFAULT_KUBERNETES_SYSTEM_NAMESPACE,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.clients.compute_cluster.client import ComputeClusterClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.compute_cluster.types import (
    DEFAULT_CLUSTER_SCHEDULER,
    ComputeClusterData,
    ComputeClusterStatus,
    ResourceGroupComputeCluster,
)
from ai.backend.manager.errors.compute_cluster import (
    ComputeClusterLost,
    ComputeClusterNotFound,
    KubernetesResourceGroupDisabled,
)
from ai.backend.manager.models.compute_cluster.row import COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.secret.pool import KeyProviderPool

type ClientFactory = Callable[[str], Awaitable[ComputeClusterClient]]


@dataclass(frozen=True)
class ComputeClusterTarget:
    name: str
    namespace_prefix: str
    client: ComputeClusterClient
    scheduler: str = DEFAULT_CLUSTER_SCHEDULER
    system_namespace: str = DEFAULT_KUBERNETES_SYSTEM_NAMESPACE


@dataclass
class _CachedClient:
    updated_at: datetime
    client: ComputeClusterClient
    users: int = 0
    retired: bool = field(default=False)


class ComputeClusterResolver:
    """Looks up the compute clusters of a batch in one query and lends their clients.

    A client is rebuilt when the cluster's registration changes; the replaced one is closed
    once no caller holds it.
    """

    _repository: SchedulerRepository
    _key_provider_pool: KeyProviderPool
    _config_provider: ManagerConfigProvider
    _client_factory: ClientFactory
    _clients: dict[str, _CachedClient]
    _lock: asyncio.Lock

    def __init__(
        self,
        repository: SchedulerRepository,
        key_provider_pool: KeyProviderPool,
        config_provider: ManagerConfigProvider,
        client_factory: ClientFactory = ComputeClusterClient.from_kubeconfig,
    ) -> None:
        self._repository = repository
        self._key_provider_pool = key_provider_pool
        self._config_provider = config_provider
        self._client_factory = client_factory
        self._clients = {}
        self._lock = asyncio.Lock()

    async def of_resource_groups(
        self, resource_groups: Collection[str]
    ) -> Mapping[str, ResourceGroupComputeCluster]:
        """The `kubernetes` resource groups among the given ones, with their clusters."""
        return await self._repository.get_compute_clusters_of_resource_groups(resource_groups)

    async def of_agents(
        self, agent_ids: Collection[AgentId]
    ) -> Mapping[AgentId, ResourceGroupComputeCluster]:
        """The agents among the given ones that are the gateway of a compute cluster."""
        return await self._repository.get_compute_clusters_of_agents(agent_ids)

    def check_launchable(self, found: ResourceGroupComputeCluster) -> ComputeClusterData:
        """The cluster a new session may be placed in, or the reason it may not."""
        if not self._config_provider.config.kubernetes.enabled:
            raise KubernetesResourceGroupDisabled(
                f"resource group {found.resource_group} runs on compute cluster"
                f" {found.cluster_name!r}"
            )
        if found.cluster is None:
            raise ComputeClusterNotFound(
                f"resource group {found.resource_group} names compute cluster"
                f" {found.cluster_name!r}, which is not registered"
            )
        if found.cluster.status == ComputeClusterStatus.LOST:
            raise ComputeClusterLost(
                f"compute cluster {found.cluster.name!r} of resource group"
                f" {found.resource_group} is LOST"
            )
        return found.cluster

    @asynccontextmanager
    async def connect(
        self, found: ResourceGroupComputeCluster, cluster: ComputeClusterData
    ) -> AsyncIterator[ComputeClusterTarget]:
        """Lend the cluster's client for the duration of the block."""
        cached = await self._acquire(cluster)
        try:
            yield ComputeClusterTarget(
                name=cluster.name,
                namespace_prefix=cluster.namespace_prefix,
                client=cached.client,
                scheduler=found.scheduler,
                system_namespace=found.system_namespace,
            )
        finally:
            await self._release(cached)

    async def close(self) -> None:
        """Close every idle client; a lent one is closed when it comes back."""
        async with self._lock:
            cached_clients = list(self._clients.values())
            self._clients.clear()
            for cached in cached_clients:
                cached.retired = True
                if cached.users == 0:
                    await cached.client.close()

    async def _acquire(self, cluster: ComputeClusterData) -> _CachedClient:
        async with self._lock:
            cached = self._clients.get(cluster.name)
            if cached is None or cached.updated_at != cluster.updated_at:
                kubeconfig = await self._key_provider_pool.decrypt(
                    cluster.kubeconfig, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
                )
                fresh = _CachedClient(
                    updated_at=cluster.updated_at, client=await self._client_factory(kubeconfig)
                )
                if cached is not None:
                    cached.retired = True
                    if cached.users == 0:
                        await cached.client.close()
                self._clients[cluster.name] = fresh
                cached = fresh
            cached.users += 1
            return cached

    async def _release(self, cached: _CachedClient) -> None:
        async with self._lock:
            cached.users -= 1
            if cached.retired and cached.users == 0:
                await cached.client.close()
