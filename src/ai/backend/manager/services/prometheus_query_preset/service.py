import logging

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import MetricPreset
from ai.backend.common.dto.clients.prometheus.response import (
    PrometheusQueryInstantResponse,
    PrometheusQueryRangeResponse,
)
from ai.backend.common.exception import PrometheusQueryPresetInvalidLabel
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
    PrometheusQueryPresetData,
)
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    CreatePresetActionResult,
    DeletePresetAction,
    DeletePresetActionResult,
    ExecutePresetAction,
    ExecutePresetActionResult,
    GetPresetAction,
    GetPresetActionResult,
    ModifyPresetAction,
    ModifyPresetActionResult,
    SearchPresetsAction,
    SearchPresetsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PrometheusQueryPresetService:
    _repository: PrometheusQueryPresetRepository
    _prometheus_client: PrometheusClient
    _default_timewindow: str

    def __init__(
        self,
        repository: PrometheusQueryPresetRepository,
        prometheus_client: PrometheusClient,
        default_timewindow: str,
    ) -> None:
        self._repository = repository
        self._prometheus_client = prometheus_client
        self._default_timewindow = default_timewindow

    async def create_preset(self, action: CreatePresetAction) -> CreatePresetActionResult:
        preset_data = await self._repository.create(action.creator)
        return CreatePresetActionResult(preset=preset_data)

    async def get_preset(self, action: GetPresetAction) -> GetPresetActionResult:
        preset_data = await self._repository.get_by_id(action.preset_id)
        return GetPresetActionResult(preset=preset_data)

    async def search_presets(self, action: SearchPresetsAction) -> SearchPresetsActionResult:
        result = await self._repository.search(action.querier)
        return SearchPresetsActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def modify_preset(self, action: ModifyPresetAction) -> ModifyPresetActionResult:
        preset_data = await self._repository.update(action.updater)
        return ModifyPresetActionResult(preset=preset_data)

    async def delete_preset(self, action: DeletePresetAction) -> DeletePresetActionResult:
        await self._repository.delete(action.preset_id)
        return DeletePresetActionResult(preset_id=action.preset_id)

    def _validate_labels(
        self,
        options: ExecutePresetOptions,
        preset_data: PrometheusQueryPresetData,
    ) -> None:
        if preset_data.filter_labels:
            invalid = set(options.filter_labels.keys()) - set(preset_data.filter_labels)
            if invalid:
                raise PrometheusQueryPresetInvalidLabel(
                    f"Invalid filter labels: {sorted(invalid)}. "
                    f"Allowed: {sorted(preset_data.filter_labels)}"
                )
        if preset_data.group_labels:
            invalid = set(options.group_labels) - set(preset_data.group_labels)
            if invalid:
                raise PrometheusQueryPresetInvalidLabel(
                    f"Invalid group labels: {sorted(invalid)}. "
                    f"Allowed: {sorted(preset_data.group_labels)}"
                )

    async def execute_preset(self, action: ExecutePresetAction) -> ExecutePresetActionResult:
        preset_data = await self._repository.get_by_id(action.preset_id)
        self._validate_labels(action.options, preset_data)
        # Window fallback: request → preset → server default
        time_window = action.time_window or preset_data.time_window or self._default_timewindow

        metric_preset = MetricPreset(
            template=preset_data.query_template,
            labels=action.options.filter_labels,
            group_by=set(action.options.group_labels),
            window=time_window,
        )
        response: PrometheusQueryRangeResponse | PrometheusQueryInstantResponse
        if action.time_range is None:
            response = await self._prometheus_client.query_instant(preset=metric_preset)
        else:
            response = await self._prometheus_client.query_range(
                preset=metric_preset,
                time_range=action.time_range,
            )
        return ExecutePresetActionResult(response=response)
