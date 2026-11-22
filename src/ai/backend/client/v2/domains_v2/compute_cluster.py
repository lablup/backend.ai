"""V2 SDK client for the compute cluster domain (superadmin only)."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    CreateComputeClusterInput,
    SearchComputeClustersInput,
    UpdateComputeClusterInput,
)
from ai.backend.common.dto.manager.v2.compute_cluster.response import (
    ComputeClusterNode,
    CreateComputeClusterPayload,
    PurgeComputeClusterPayload,
    SearchComputeClustersPayload,
    UpdateComputeClusterPayload,
)

_PATH: Final = "/v2/compute-clusters"


class V2ComputeClusterClient(BaseDomainClient):
    """SDK client for compute cluster operations. The kubeconfig is sent, never returned."""

    async def admin_create(self, request: CreateComputeClusterInput) -> CreateComputeClusterPayload:
        """Register a compute cluster."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateComputeClusterPayload,
        )

    async def admin_search(
        self, request: SearchComputeClustersInput
    ) -> SearchComputeClustersPayload:
        """Search compute clusters with filter/order/pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchComputeClustersPayload,
        )

    async def admin_get(self, compute_cluster_id: UUID) -> ComputeClusterNode:
        """Get a compute cluster by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{compute_cluster_id}",
            response_model=ComputeClusterNode,
        )

    async def admin_update(
        self,
        compute_cluster_id: UUID,
        request: UpdateComputeClusterInput,
    ) -> UpdateComputeClusterPayload:
        """Update a compute cluster."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{compute_cluster_id}",
            request=request,
            response_model=UpdateComputeClusterPayload,
        )

    async def admin_purge(self, compute_cluster_id: UUID) -> PurgeComputeClusterPayload:
        """Permanently remove a compute cluster."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{compute_cluster_id}",
            response_model=PurgeComputeClusterPayload,
        )
