"""REST v2 handler for the prometheus query preset domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    CreateQueryDefinitionInput,
    DeleteQueryDefinitionInput,
    ExecuteQueryDefinitionInput,
    ModifyQueryDefinitionInput,
    SearchQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    ExecuteQueryDefinitionPayload,
    QueryDefinitionExecuteDataInfo,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import PresetIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.prometheus_query_preset import PrometheusQueryPresetAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2PrometheusQueryPresetHandler:
    """REST v2 handler for prometheus query preset operations."""

    def __init__(self, *, adapter: PrometheusQueryPresetAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateQueryDefinitionInput],
    ) -> APIResponse:
        """Create a new prometheus query definition."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def search(
        self,
        body: BodyParam[SearchQueryDefinitionsInput],
    ) -> APIResponse:
        """Search prometheus query presets.

        Available to any authenticated user since presets are a shared
        catalog of metric query templates.
        """
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        """Get a single query definition by ID."""
        result = await self._adapter.get(path.parsed.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[PresetIdPathParam],
        body: BodyParam[ModifyQueryDefinitionInput],
    ) -> APIResponse:
        """Update an existing query definition."""
        result = await self._adapter.update(path.parsed.preset_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def execute(
        self,
        path: PathParam[PresetIdPathParam],
        body: BodyParam[ExecuteQueryDefinitionInput],
    ) -> APIResponse:
        """Execute a prometheus query definition."""
        result = await self._adapter.execute_preset(
            path.parsed.preset_id,
            body.parsed.options,
            body.parsed.time_window,
            body.parsed.time_range,
        )
        payload = ExecuteQueryDefinitionPayload(
            status=result.status,
            data=QueryDefinitionExecuteDataInfo(
                result_type=result.result_type,
                result=result.result,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def delete(
        self,
        body: BodyParam[DeleteQueryDefinitionInput],
    ) -> APIResponse:
        """Delete a query definition by ID."""
        result = await self._adapter.delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
