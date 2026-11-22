"""REST v2 handler for the compute cluster domain (superadmin only)."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    CreateComputeClusterInput,
    SearchComputeClustersInput,
    UpdateComputeClusterInput,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import ComputeClusterIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.compute_cluster.adapter import ComputeClusterAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class V2ComputeClusterHandler:
    """REST v2 handler for compute cluster operations."""

    _adapter: ComputeClusterAdapter

    def __init__(self, *, adapter: ComputeClusterAdapter) -> None:
        self._adapter = adapter

    async def admin_create(
        self,
        body: BodyParam[CreateComputeClusterInput],
    ) -> APIResponse:
        """Register a compute cluster."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchComputeClustersInput],
    ) -> APIResponse:
        """Search compute clusters with filter/order/pagination."""
        result = await self._adapter.global_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_get(
        self,
        path: PathParam[ComputeClusterIdPathParam],
    ) -> APIResponse:
        """Get a compute cluster by id."""
        result = await self._adapter.get(path.parsed.compute_cluster_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_update(
        self,
        path: PathParam[ComputeClusterIdPathParam],
        body: BodyParam[UpdateComputeClusterInput],
    ) -> APIResponse:
        """Update a compute cluster."""
        result = await self._adapter.update(path.parsed.compute_cluster_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_purge(
        self,
        path: PathParam[ComputeClusterIdPathParam],
    ) -> APIResponse:
        """Permanently remove a compute cluster."""
        result = await self._adapter.purge(path.parsed.compute_cluster_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
