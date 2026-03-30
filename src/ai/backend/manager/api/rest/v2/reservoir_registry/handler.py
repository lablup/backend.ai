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
    UpdateReservoirRegistryInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import RegistryIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.reservoir_registry import ReservoirRegistryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


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

    async def delete(
        self,
        body: BodyParam[DeleteReservoirRegistryInput],
    ) -> APIResponse:
        """Delete a Reservoir registry."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
