"""V2 SDK client for the prometheus query preset category domain."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CreateCategoryInput,
    DeleteCategoryInput,
    SearchCategoriesInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    CreateCategoryPayload,
    DeleteCategoryPayload,
    GetCategoryPayload,
    SearchCategoriesPayload,
)

_PATH = "/v2/prometheus-query-preset-categories"


class V2PrometheusQueryPresetCategoryClient(BaseDomainClient):
    """SDK client for prometheus query preset category operations."""

    async def create(self, request: CreateCategoryInput) -> CreateCategoryPayload:
        """Create a new prometheus query preset category."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateCategoryPayload,
        )

    async def search(self, request: SearchCategoriesInput) -> SearchCategoriesPayload:
        """Search categories with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchCategoriesPayload,
        )

    async def get(self, category_id: UUID) -> GetCategoryPayload:
        """Get a single category by ID."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{category_id}",
            response_model=GetCategoryPayload,
        )

    async def delete(self, request: DeleteCategoryInput) -> DeleteCategoryPayload:
        """Delete a category by ID."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteCategoryPayload,
        )
