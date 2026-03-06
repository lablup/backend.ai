"""REST API handler for Prometheus Query Preset operations."""

from __future__ import annotations

from http import HTTPStatus

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam, Sentinel
from ai.backend.common.dto.manager.prometheus_query_preset import (
    CreatePresetRequest,
    CreatePresetResponse,
    DeletePresetResponse,
    ExecutePresetRequest,
    ExecutePresetResponse,
    GetPresetResponse,
    ModifyPresetRequest,
    ModifyPresetResponse,
    PaginationInfo,
    PresetExecuteData,
    PresetIdPathParam,
    SearchPresetsRequest,
    SearchPresetsResponse,
)
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
)
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.repositories.base import (
    Creator,
    Updater,
)
from ai.backend.manager.repositories.prometheus_query_preset.creators import (
    PrometheusQueryPresetCreatorSpec,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.services.prometheus_query_preset.actions.create import (
    CreatePresetAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.delete import (
    DeletePresetAction,
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
from ai.backend.manager.services.prometheus_query_preset.actions.search import (
    SearchPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.processors import (
    PrometheusQueryPresetProcessors,
)
from ai.backend.manager.types import OptionalState, TriState

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
        body: BodyParam[CreatePresetRequest],
    ) -> APIResponse:
        """Create a new prometheus query preset."""
        creator: Creator[PrometheusQueryPresetRow] = Creator(
            spec=PrometheusQueryPresetCreatorSpec(
                name=body.parsed.name,
                metric_name=body.parsed.metric_name,
                query_template=body.parsed.query_template,
                time_window=body.parsed.time_window,
                filter_labels=body.parsed.options.filter_labels,
                group_labels=body.parsed.options.group_labels,
            )
        )
        action_result = await self._processor.create_preset.wait_for_complete(
            CreatePresetAction(creator=creator)
        )
        resp = CreatePresetResponse(item=self._adapter.convert_to_dto(action_result.preset))
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=resp)

    async def search_presets(
        self,
        body: BodyParam[SearchPresetsRequest],
    ) -> APIResponse:
        """Search presets with filters, orders, and pagination."""
        querier = self._adapter.build_querier(body.parsed)
        action_result = await self._processor.search_presets.wait_for_complete(
            SearchPresetsAction(querier=querier)
        )
        resp = SearchPresetsResponse(
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
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        """Get a preset by ID."""
        action_result = await self._processor.get_preset.wait_for_complete(
            GetPresetAction(preset_id=path.parsed.id)
        )
        resp = GetPresetResponse(item=self._adapter.convert_to_dto(action_result.preset))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def modify_preset(
        self,
        path: PathParam[PresetIdPathParam],
        body: BodyParam[ModifyPresetRequest],
    ) -> APIResponse:
        """Modify a preset."""
        parsed = body.parsed
        updater_spec = PrometheusQueryPresetUpdaterSpec(
            name=(
                OptionalState.update(parsed.name)
                if parsed.name is not None
                else OptionalState.nop()
            ),
            metric_name=(
                OptionalState.update(parsed.metric_name)
                if parsed.metric_name is not None
                else OptionalState.nop()
            ),
            query_template=(
                OptionalState.update(parsed.query_template)
                if parsed.query_template is not None
                else OptionalState.nop()
            ),
            time_window=TriState.nop()
            if isinstance(parsed.time_window, Sentinel)
            else TriState.nullify()
            if parsed.time_window is None
            else TriState.update(parsed.time_window),
            filter_labels=(
                OptionalState.update(parsed.options.filter_labels)
                if parsed.options is not None and parsed.options.filter_labels is not None
                else OptionalState.nop()
            ),
            group_labels=(
                OptionalState.update(parsed.options.group_labels)
                if parsed.options is not None and parsed.options.group_labels is not None
                else OptionalState.nop()
            ),
        )
        updater: Updater[PrometheusQueryPresetRow] = Updater(
            spec=updater_spec, pk_value=path.parsed.id
        )
        action_result = await self._processor.modify_preset.wait_for_complete(
            ModifyPresetAction(preset_id=path.parsed.id, updater=updater)
        )
        resp = ModifyPresetResponse(item=self._adapter.convert_to_dto(action_result.preset))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def delete_preset(
        self,
        path: PathParam[PresetIdPathParam],
    ) -> APIResponse:
        """Delete a preset."""
        action_result = await self._processor.delete_preset.wait_for_complete(
            DeletePresetAction(preset_id=path.parsed.id)
        )
        resp = DeletePresetResponse(id=action_result.preset_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def execute_preset(
        self,
        path: PathParam[PresetIdPathParam],
        body: BodyParam[ExecutePresetRequest],
    ) -> APIResponse:
        """Execute a preset with given parameters."""
        filter_labels = {entry.key: entry.value for entry in body.parsed.options.filter_labels}
        options = ExecutePresetOptions(
            filter_labels=filter_labels,
            group_labels=body.parsed.options.group_labels,
        )

        action_result = await self._processor.execute_preset.wait_for_complete(
            ExecutePresetAction(
                preset_id=path.parsed.id,
                options=options,
                window=body.parsed.window,
                time_range=body.parsed.time_range,
            )
        )

        prom_response = action_result.response
        result_items = [
            self._adapter.convert_metric_response(metric_response)
            for metric_response in prom_response.data.result
        ]
        resp = ExecutePresetResponse(
            status=prom_response.status,
            data=PresetExecuteData(
                result_type=prom_response.data.result_type,
                result=result_items,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
