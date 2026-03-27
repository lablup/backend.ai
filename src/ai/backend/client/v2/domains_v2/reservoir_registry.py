"""V2 REST SDK client for the Reservoir registry resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.reservoir_registry.request import (
    AdminSearchReservoirRegistriesInput,
    CreateReservoirRegistryInput,
    DeleteReservoirRegistryInput,
    UpdateReservoirRegistryInput,
)
from ai.backend.common.dto.manager.v2.reservoir_registry.response import (
    AdminSearchReservoirRegistriesPayload,
    CreateReservoirRegistryPayload,
    DeleteReservoirRegistryPayload,
    ReservoirRegistryNode,
    UpdateReservoirRegistryPayload,
)

_PATH = "/v2/reservoir-registries"


class V2ReservoirRegistryClient(BaseDomainClient):
    """SDK client for ``/v2/reservoir-registries`` endpoints."""

    async def create(
        self,
        request: CreateReservoirRegistryInput,
    ) -> CreateReservoirRegistryPayload:
        """Create a new Reservoir registry."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateReservoirRegistryPayload,
        )

    async def search(
        self,
        request: AdminSearchReservoirRegistriesInput,
    ) -> AdminSearchReservoirRegistriesPayload:
        """Search Reservoir registries with pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchReservoirRegistriesPayload,
        )

    async def get(self, registry_id: UUID) -> ReservoirRegistryNode:
        """Get a single Reservoir registry by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{registry_id}",
            response_model=ReservoirRegistryNode,
        )

    async def update(
        self,
        request: UpdateReservoirRegistryInput,
    ) -> UpdateReservoirRegistryPayload:
        """Update an existing Reservoir registry."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{request.id}",
            request=request,
            response_model=UpdateReservoirRegistryPayload,
        )

    async def delete(
        self,
        request: DeleteReservoirRegistryInput,
    ) -> DeleteReservoirRegistryPayload:
        """Delete a Reservoir registry."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteReservoirRegistryPayload,
        )
