"""Which compute cluster a session runs in, for the launcher and the terminator.

A resource group whose driver is `kubernetes` names its cluster in `driver_opts.compute_cluster`;
the cluster's only agent is its session gateway.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
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
)
from ai.backend.manager.errors.compute_cluster import KubernetesResourceGroupDisabled
from ai.backend.manager.models.compute_cluster.row import COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.secret.pool import KeyProviderPool


@dataclass(frozen=True)
class ComputeClusterTarget:
    name: str
    namespace_prefix: str
    client: ComputeClusterClient
    scheduler: str = DEFAULT_CLUSTER_SCHEDULER
    system_namespace: str = DEFAULT_KUBERNETES_SYSTEM_NAMESPACE


class ComputeClusterResolver:
    _repository: SchedulerRepository
    _key_provider_pool: KeyProviderPool
    _config_provider: ManagerConfigProvider
    _clients: dict[str, tuple[datetime, ComputeClusterClient]]
    _lock: asyncio.Lock

    def __init__(
        self,
        repository: SchedulerRepository,
        key_provider_pool: KeyProviderPool,
        config_provider: ManagerConfigProvider,
    ) -> None:
        self._repository = repository
        self._key_provider_pool = key_provider_pool
        self._config_provider = config_provider
        self._clients = {}
        self._lock = asyncio.Lock()

    async def for_resource_group(self, resource_group: str) -> ComputeClusterTarget | None:
        found = await self._repository.get_compute_cluster_of_resource_group(resource_group)
        if found is None:
            return None
        cluster = found.cluster
        if not self._config_provider.config.kubernetes.enabled:
            raise KubernetesResourceGroupDisabled(
                f"resource group {resource_group} runs on compute cluster {cluster.name}"
            )
        return ComputeClusterTarget(
            name=cluster.name,
            namespace_prefix=cluster.namespace_prefix,
            client=await self._client(cluster),
            scheduler=found.scheduler,
            system_namespace=found.system_namespace,
        )

    async def for_agent(self, agent_id: AgentId) -> ComputeClusterTarget | None:
        resource_group = await self._repository.get_resource_group_of_agent(agent_id)
        if resource_group is None:
            return None
        return await self.for_resource_group(resource_group)

    async def close(self) -> None:
        for _, client in self._clients.values():
            await client.close()

    async def _client(self, cluster: ComputeClusterData) -> ComputeClusterClient:
        """One client per cluster, rebuilt when the registration changes."""
        async with self._lock:
            cached = self._clients.get(cluster.name)
            if cached is not None and cached[0] == cluster.updated_at:
                return cached[1]
            kubeconfig = await self._key_provider_pool.decrypt(
                cluster.kubeconfig, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
            )
            client = await ComputeClusterClient.from_kubeconfig(kubeconfig)
            if cached is not None:
                await cached[1].close()
            self._clients[cluster.name] = (cluster.updated_at, client)
            return client
