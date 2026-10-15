"""REST v2 handler for the prometheus query preset category domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryID,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CreateCategoryInput,
    DeleteCategoryInput,
    PartialBulkPurgeQueryPresetCategoriesInput,
    SearchCategoriesInput,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import CategoryIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
        PrometheusQueryPresetCategoryAdapter,
    )

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class V2PrometheusQueryPresetCategoryHandler:
    """REST v2 handler for prometheus query preset category operations."""

    def __init__(self, *, adapter: PrometheusQueryPresetCategoryAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateCategoryInput],
    ) -> APIResponse:
        """Create a new prometheus query preset category."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search(
        self,
        body: BodyParam[SearchCategoriesInput],
    ) -> APIResponse:
        """Search prometheus query preset categories.

        Available to any authenticated user since categories are a shared
        catalog for organizing metric query templates.
        """
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[CategoryIdPathParam],
    ) -> APIResponse:
        """Get a single category by ID."""
        result = await self._adapter.get(path.parsed.category_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[CategoryIdPathParam],
    ) -> APIResponse:
        """Permanently remove a category."""
        result = await self._adapter.purge(PrometheusQueryPresetCategoryID(path.parsed.category_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeQueryPresetCategoriesInput],
    ) -> APIResponse:
        """Permanently remove several categories, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        body: BodyParam[DeleteCategoryInput],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/prometheus-query-preset-categories/{category_id}`."""
        result = await self._adapter.purge(PrometheusQueryPresetCategoryID(body.parsed.id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
