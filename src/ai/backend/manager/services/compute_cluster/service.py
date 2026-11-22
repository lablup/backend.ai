from __future__ import annotations

from dataclasses import replace

from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult, EntityOpsResult
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.creators import ComputeClusterCreator
from ai.backend.manager.models.compute_cluster.row import COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.compute_cluster.actions.create import (
    CreateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.update import (
    UpdateComputeClusterAction,
)
from ai.backend.manager.types import OptionalState

__all__ = ("ComputeClusterService",)


class ComputeClusterService:
    """The writes that carry a kubeconfig, which is encrypted before it reaches the spec.

    Get, search and purge run straight against ops.
    """

    _ops_repository: OpsRepository[ComputeClusterData]
    _key_provider_pool: KeyProviderPool

    def __init__(
        self,
        ops_repository: OpsRepository[ComputeClusterData],
        key_provider_pool: KeyProviderPool,
    ) -> None:
        self._ops_repository = ops_repository
        self._key_provider_pool = key_provider_pool

    async def create(
        self, action: CreateComputeClusterAction
    ) -> CreatedEntityOpsResult[ComputeClusterData]:
        kubeconfig = await self._key_provider_pool.encrypt(
            action.kubeconfig, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
        )
        creator = ComputeClusterCreator(
            name=action.name,
            description=action.description,
            api_server=action.api_server,
            kubeconfig=kubeconfig,
            namespace_prefix=action.namespace_prefix,
            gateway_addr=action.gateway_addr,
            gateway_public_key=action.gateway_public_key,
        )
        return CreatedEntityOpsResult(data=await self._ops_repository.create_entity(creator))

    async def update(
        self, action: UpdateComputeClusterAction
    ) -> EntityOpsResult[ComputeClusterData]:
        updater = action.updater
        plaintext = action.kubeconfig.optional_value()
        if plaintext is not None:
            encrypted = await self._key_provider_pool.encrypt(
                plaintext, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
            )
            updater = replace(updater, kubeconfig=OptionalState.update(encrypted))
        return EntityOpsResult(data=await self._ops_repository.update(updater))
