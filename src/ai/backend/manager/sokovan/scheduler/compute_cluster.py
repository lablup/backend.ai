"""Which compute cluster a session runs in, for the launcher and the terminator.

A resource group whose driver is `kubernetes` names its cluster in `driver_opts.compute_cluster`;
the cluster's only agent is its session gateway.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Collection, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Final

import aiohttp

from ai.backend.common.dto.manager.v2.resource_group.request import (
    DEFAULT_KUBERNETES_SYSTEM_NAMESPACE,
)
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.clients.compute_cluster.client import ComputeClusterClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.compute_cluster.types import (
    DEFAULT_CLUSTER_SCHEDULER,
    ComputeClusterData,
    ComputeClusterStatus,
    ResourceGroupComputeCluster,
)
from ai.backend.manager.errors.compute_cluster import (
    ComputeClusterKubeconfigInvalid,
    ComputeClusterLost,
    ComputeClusterNotFound,
    InvalidKubeconfig,
    KubernetesResourceGroupDisabled,
)
from ai.backend.manager.models.compute_cluster.row import COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.secret.pool import KeyProviderPool

log = StructuredLogger(logging.getLogger(__spec__.name))

type ClientFactory = Callable[[str], Awaitable[ComputeClusterClient]]

CONNECTION_FAILURES_BEFORE_LOST: Final = 5
"""Consecutive API connection failures after which a compute cluster is marked LOST."""


def is_connection_failure(error: BaseException) -> bool:
    """Whether the API server could not be reached, as opposed to answering with an error."""
    return isinstance(error, (aiohttp.ClientError, TimeoutError, OSError))


@dataclass(frozen=True)
class ComputeClusterLookup[K]:
    """The compute clusters found for a batch, and the keys whose lookup failed; a key
    that is in neither is not on a `kubernetes` resource group."""

    found: Mapping[K, ResourceGroupComputeCluster]
    unresolved: frozenset[K] = frozenset()


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
    _connection_failures: dict[str, int]

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
        self._connection_failures = {}

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

    async def lookup_resource_groups(
        self, resource_groups: Collection[str]
    ) -> ComputeClusterLookup[str]:
        """`of_resource_groups`, isolating a failing lookup: when the batch query fails each
        resource group is looked up alone, and the ones that still fail are `unresolved`."""
        if not resource_groups:
            return ComputeClusterLookup(found={})
        try:
            return ComputeClusterLookup(found=await self.of_resource_groups(resource_groups))
        except Exception as e:
            log.warning(
                "compute cluster lookup of resource groups failed",
                resource_group_count=len(resource_groups),
                exc_info=e,
            )
        found: dict[str, ResourceGroupComputeCluster] = {}
        unresolved: set[str] = set()
        for resource_group in resource_groups:
            try:
                found.update(await self.of_resource_groups([resource_group]))
            except Exception:
                unresolved.add(resource_group)
        return ComputeClusterLookup(found=found, unresolved=frozenset(unresolved))

    async def lookup_agents(self, agent_ids: Collection[AgentId]) -> ComputeClusterLookup[AgentId]:
        """`of_agents`, isolating a failing lookup as `lookup_resource_groups` does."""
        if not agent_ids:
            return ComputeClusterLookup(found={})
        try:
            return ComputeClusterLookup(found=await self.of_agents(agent_ids))
        except Exception as e:
            log.warning(
                "compute cluster lookup of agents failed",
                agent_count=len(agent_ids),
                exc_info=e,
            )
        found: dict[AgentId, ResourceGroupComputeCluster] = {}
        unresolved: set[AgentId] = set()
        for agent_id in agent_ids:
            try:
                found.update(await self.of_agents([agent_id]))
            except Exception:
                unresolved.add(agent_id)
        return ComputeClusterLookup(found=found, unresolved=frozenset(unresolved))

    async def revive_if_reachable(
        self, found: ResourceGroupComputeCluster
    ) -> ResourceGroupComputeCluster:
        """Probe a LOST cluster once; when its API server answers it is ALIVE again.

        A LOST cluster gets no new sessions, so without this nothing would reach it to
        notice that it is back.
        """
        cluster = found.cluster
        if (
            cluster is None
            or cluster.status != ComputeClusterStatus.LOST
            or not self._config_provider.config.kubernetes.enabled
        ):
            return found
        try:
            async with self.connect(found, cluster) as target:
                await target.client.probe()
        except Exception as e:
            log.debug("lost compute cluster still unreachable", compute_cluster=cluster.name)
            if not is_connection_failure(e):
                log.warning(
                    "lost compute cluster probe failed", compute_cluster=cluster.name, exc_info=e
                )
            return found
        return replace(found, cluster=replace(cluster, status=ComputeClusterStatus.ALIVE))

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
        """Lend the cluster's client for the duration of the block.

        Raises ComputeClusterKubeconfigInvalid when the stored kubeconfig no longer
        validates. A connection failure in the block counts toward marking the cluster
        LOST; a block that completes marks it ALIVE.
        """
        try:
            cached = await self._acquire(cluster)
        except InvalidKubeconfig as e:
            raise ComputeClusterKubeconfigInvalid(
                f"the stored kubeconfig of compute cluster {cluster.name!r} no longer"
                f" validates: {e}"
            ) from e
        try:
            yield ComputeClusterTarget(
                name=cluster.name,
                namespace_prefix=cluster.namespace_prefix,
                client=cached.client,
                scheduler=found.scheduler,
                system_namespace=found.system_namespace,
            )
        except Exception as e:
            if is_connection_failure(e):
                await self._record_connection_failure(cluster)
            raise
        else:
            await self._record_reachable(cluster)
        finally:
            await self._release(cached)

    async def _record_connection_failure(self, cluster: ComputeClusterData) -> None:
        failures = self._connection_failures.get(cluster.name, 0) + 1
        self._connection_failures[cluster.name] = failures
        if (
            failures < CONNECTION_FAILURES_BEFORE_LOST
            or cluster.status == ComputeClusterStatus.LOST
        ):
            return
        if await self._update_status(cluster, ComputeClusterStatus.LOST):
            log.warning(
                "compute cluster marked lost",
                compute_cluster=cluster.name,
                failure_count=failures,
            )

    async def _record_reachable(self, cluster: ComputeClusterData) -> None:
        self._connection_failures.pop(cluster.name, None)
        if cluster.status == ComputeClusterStatus.ALIVE:
            return
        if await self._update_status(cluster, ComputeClusterStatus.ALIVE):
            log.info("compute cluster alive", compute_cluster=cluster.name)

    async def _update_status(
        self, cluster: ComputeClusterData, status: ComputeClusterStatus
    ) -> bool:
        """Write the status; a failed write is retried by the next call through the cluster."""
        try:
            return await self._repository.update_compute_cluster_status(cluster.id, status)
        except Exception as e:
            log.warning(
                "compute cluster status update failed",
                compute_cluster=cluster.name,
                status=status,
                exc_info=e,
            )
            return False

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
