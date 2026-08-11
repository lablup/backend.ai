"""REST API handler for Prometheus Query Preset operations."""

from __future__ import annotations

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.prometheus_query_preset import (
    CreateQueryDefinitionRequest,
    CreateQueryDefinitionResponse,
    DeleteQueryDefinitionResponse,
    ExecuteQueryDefinitionRequest,
    ExecuteQueryDefinitionResponse,
    GetQueryDefinitionResponse,
    ModifyQueryDefinitionRequest,
    ModifyQueryDefinitionResponse,
    PaginationInfo,
    QueryDefinitionExecuteData,
    QueryDefinitionIdPathParam,
    SearchQueryDefinitionsRequest,
    SearchQueryDefinitionsResponse,
)
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
)
from ai.backend.manager.models.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreator,
)
from ai.backend.manager.services.prometheus_query_preset.actions.create import (
    CreatePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.execute_preset import (
    ExecutePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.get import (
    GetPresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.modify import (
    ModifyPresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.purge import (
    PurgePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.search import (
    SearchPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)

from .adapter import PrometheusQueryPresetAdapter


class PrometheusQueryPresetHandler:
    """REST API handler for Prometheus Query Preset CRUD and execution."""

    def __init__(
        self,
        *,
        processor: PrometheusQueryPresetProcessors,
    ) -> None:
        self._processor = processor
        self._adapter = PrometheusQueryPresetAdapter()

    async def create_preset(
        self,
        body: BodyParam[CreateQueryDefinitionRequest],
    ) -> APIResponse:
        """Create a new prometheus query preset."""
        creator = PrometheusQueryPresetCreator(
            name=body.parsed.name,
            metric_name=body.parsed.metric_name,
            query_template=body.parsed.query_template,
            time_window=body.parsed.time_window,
            filter_labels=body.parsed.options.filter_labels,
            group_labels=body.parsed.options.group_labels,
        )
        action_result = await self._processor.create_preset.run(CreatePresetAction(creator=creator))
        resp = CreateQueryDefinitionResponse(item=self._adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_presets(
        self,
        body: BodyParam[SearchQueryDefinitionsRequest],
    ) -> APIResponse:
        """Search presets with filters, orders, and pagination."""
        searcher = self._adapter.build_searcher(body.parsed)
        action_result = await self._processor.search_presets.run(
            SearchPresetsAction(searcher=searcher)
        )
        resp = SearchQueryDefinitionsResponse(
            items=[
                self._adapter.convert_to_dto(preset_data) for preset_data in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def get_preset(
        self,
        path: PathParam[QueryDefinitionIdPathParam],
    ) -> APIResponse:
        """Get a preset by ID."""
        action_result = await self._processor.get_preset.run(
            GetPresetAction(preset_id=PrometheusQueryPresetID(path.parsed.id))
        )
        resp = GetQueryDefinitionResponse(item=self._adapter.convert_to_dto(action_result.data))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def modify_preset(
        self,
        path: PathParam[QueryDefinitionIdPathParam],
        body: BodyParam[ModifyQueryDefinitionRequest],
    ) -> APIResponse:
        """Modify a preset."""
        updater = self._adapter.build_updater(body.parsed, path.parsed.id)
        action_result = await self._processor.modify_preset.run(
            ModifyPresetAction(preset_id=PrometheusQueryPresetID(path.parsed.id), updater=updater)
        )
        resp = ModifyQueryDefinitionResponse(
            item=self._adapter.convert_to_dto(action_result.preset)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_preset(
        self,
        path: PathParam[QueryDefinitionIdPathParam],
    ) -> APIResponse:
        """Delete a preset."""
        action_result = await self._processor.purge_preset.run(
            PurgePresetAction(preset_id=PrometheusQueryPresetID(path.parsed.id))
        )
        resp = DeleteQueryDefinitionResponse(id=action_result.data.id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def execute_preset(
        self,
        path: PathParam[QueryDefinitionIdPathParam],
        body: BodyParam[ExecuteQueryDefinitionRequest],
    ) -> APIResponse:
        """Execute a preset with given parameters."""
        filter_labels = {entry.key: entry.value for entry in body.parsed.options.filter_labels}
        options = ExecutePresetOptions(
            filter_labels=filter_labels,
            group_labels=body.parsed.options.group_labels,
        )

        action_result = await self._processor.execute_preset.run(
            ExecutePresetAction(
                preset_id=path.parsed.id,
                options=options,
                time_window=body.parsed.time_window,
                time_range=body.parsed.time_range,
            )
        )

        prom_response = action_result.response
        result_items = [
            self._adapter.convert_metric_response(metric_response)
            for metric_response in prom_response.data.result
        ]
        resp = ExecuteQueryDefinitionResponse(
            status=prom_response.status,
            data=QueryDefinitionExecuteData(
                result_type=prom_response.data.result_type,
                result=result_items,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
