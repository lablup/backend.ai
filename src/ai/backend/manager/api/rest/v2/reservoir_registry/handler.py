"""REST v2 handler for the Reservoir registry domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
    CreateReservoirRegistryInput,
    DeleteReservoirRegistryInput,
    PartialBulkPurgeReservoirRegistriesInput,
    PartialBulkUpdateReservoirRegistriesInput,
    UpdateReservoirRegistryInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    DeleteReservoirRegistryPayload,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import RegistryIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.reservoir_registry.adapter import ReservoirRegistryAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class V2ReservoirRegistryHandler:
    """REST v2 handler for Reservoir registry operations."""

    def __init__(self, *, adapter: ReservoirRegistryAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateReservoirRegistryInput],
    ) -> APIResponse:
        """Create a new Reservoir registry."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search(
        self,
        body: BodyParam[AdminSearchReservoirRegistriesInput],
    ) -> APIResponse:
        """Search Reservoir registries with pagination."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[RegistryIdPathParam],
    ) -> APIResponse:
        """Get a single Reservoir registry by ID."""
        result = await self._adapter.get(path.parsed.registry_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        body: BodyParam[UpdateReservoirRegistryInput],
    ) -> APIResponse:
        """Update an existing Reservoir registry."""
        result = await self._adapter.update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[RegistryIdPathParam],
    ) -> APIResponse:
        """Permanently delete a Reservoir registry."""
        result = await self._adapter.purge(path.parsed.registry_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update(
        self,
        body: BodyParam[PartialBulkUpdateReservoirRegistriesInput],
    ) -> APIResponse:
        """Update several Reservoir registries, answering for each one."""
        result = await self._adapter.partial_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeReservoirRegistriesInput],
    ) -> APIResponse:
        """Permanently delete several Reservoir registries, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteReservoirRegistryInput],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/reservoir-registries/{registry_id}`."""
        result = await self._adapter.purge(body.parsed.id)
        return APIResponse.build(
            status_code=HTTPStatus.OK,
            response_model=DeleteReservoirRegistryPayload(id=result.id, entity_id=result.entity_id),
        )
