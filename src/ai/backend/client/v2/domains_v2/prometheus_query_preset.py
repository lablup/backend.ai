"""V2 SDK client for the prometheus query preset domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    DeleteQueryDefinitionInput,
    ModifyQueryDefinitionInput,
    SearchQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    AdminSearchQueryDefinitionsPayload,
    CreateQueryDefinitionPayload,
    DeleteQueryDefinitionPayload,
    GetQueryDefinitionPayload,
    ModifyQueryDefinitionPayload,
)

_PATH = "/v2/prometheus-query-presets"


class V2PrometheusQueryPresetClient(BaseDomainClient):
    """SDK client for prometheus query preset operations."""

    async def create(self, request: CreateQueryDefinitionInput) -> CreateQueryDefinitionPayload:
        """Create a new prometheus query definition."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateQueryDefinitionPayload,
        )

    async def search(
        self, request: SearchQueryDefinitionsInput
    ) -> AdminSearchQueryDefinitionsPayload:
        """Search query definitions with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchQueryDefinitionsPayload,
        )

    async def get(self, preset_id: UUID) -> GetQueryDefinitionPayload:
        """Get a single query definition by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{preset_id}",
            response_model=GetQueryDefinitionPayload,
        )

    async def update(
        self, preset_id: UUID, request: ModifyQueryDefinitionInput
    ) -> ModifyQueryDefinitionPayload:
        """Update an existing query definition."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{preset_id}",
            request=request,
            response_model=ModifyQueryDefinitionPayload,
        )

    async def delete(self, request: DeleteQueryDefinitionInput) -> DeleteQueryDefinitionPayload:
        """Delete a query definition by ID."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteQueryDefinitionPayload,
        )
