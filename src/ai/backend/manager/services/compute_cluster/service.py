from __future__ import annotations

from dataclasses import replace

from ai.backend.common.dto.manager.v2.compute_cluster.kubeconfig import (
    InvalidKubeconfigError,
    ParsedKubeconfig,
    parse_kubeconfig,
)
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult, EntityOpsResult
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.errors.compute_cluster import InvalidKubeconfig
from ai.backend.manager.models.compute_cluster.creators import ComputeClusterCreator
from ai.backend.manager.models.compute_cluster.row import COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.compute_cluster.actions.create import (
    CreateComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.purge import (
    PurgeComputeClusterAction,
)
from ai.backend.manager.services.compute_cluster.actions.update import (
    UpdateComputeClusterAction,
)
from ai.backend.manager.types import OptionalState

__all__ = ("ComputeClusterService",)


def _validate_kubeconfig(kubeconfig: str, api_server: str | None) -> ParsedKubeconfig:
    """The kubeconfig's current context; a given ``api_server`` must be its server."""
    try:
        parsed = parse_kubeconfig(kubeconfig)
    except InvalidKubeconfigError as e:
        raise InvalidKubeconfig(str(e)) from e
    if api_server is not None and api_server.rstrip("/") != parsed.server.rstrip("/"):
        raise InvalidKubeconfig(
            f"api_server {api_server!r} differs from the kubeconfig's server {parsed.server!r}"
        )
    return parsed


class ComputeClusterService:
    """The writes that carry a kubeconfig, which is validated and encrypted before it reaches
    the spec. The API server is always the kubeconfig's.

    The purge is ordered against a resource group write naming the cluster. Get and search
    run straight against ops.
    """

    _ops_repository: OpsRepository[ComputeClusterData]
    _resource_group_repository: ResourceGroupRepository
    _key_provider_pool: KeyProviderPool

    def __init__(
        self,
        ops_repository: OpsRepository[ComputeClusterData],
        resource_group_repository: ResourceGroupRepository,
        key_provider_pool: KeyProviderPool,
    ) -> None:
        self._ops_repository = ops_repository
        self._resource_group_repository = resource_group_repository
        self._key_provider_pool = key_provider_pool

    async def create(
        self, action: CreateComputeClusterAction
    ) -> CreatedEntityOpsResult[ComputeClusterData]:
        parsed = _validate_kubeconfig(action.kubeconfig, action.api_server)
        kubeconfig = await self._key_provider_pool.encrypt(
            action.kubeconfig, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
        )
        creator = ComputeClusterCreator(
            name=action.name,
            description=action.description,
            api_server=parsed.server,
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
        requested_server = updater.api_server.optional_value()
        plaintext = action.kubeconfig.optional_value()
        if plaintext is None:
            if requested_server is not None:
                raise InvalidKubeconfig(
                    "api_server is read from the kubeconfig; send the kubeconfig instead"
                )
        else:
            parsed = _validate_kubeconfig(plaintext, requested_server)
            encrypted = await self._key_provider_pool.encrypt(
                plaintext, COMPUTE_CLUSTER_KUBECONFIG_CONTEXT
            )
            updater = replace(
                updater,
                kubeconfig=OptionalState.update(encrypted),
                api_server=OptionalState.update(parsed.server),
            )
        return EntityOpsResult(data=await self._ops_repository.update(updater))

    async def purge(self, action: PurgeComputeClusterAction) -> EntityOpsResult[ComputeClusterData]:
        return EntityOpsResult(
            data=await self._resource_group_repository.purge_compute_cluster(action.to_purger())
        )
