import logging
import re

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import MetricPreset
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.logging.utils import BraceStyleAdapter
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

_WINDOW_PATTERN = re.compile(r"^\d+[smhdw]$")


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
        preset_id = await self._repository.delete(action.preset_id)
        return DeletePresetActionResult(preset_id=preset_id)

    async def execute_preset(self, action: ExecutePresetAction) -> ExecutePresetActionResult:
        preset_data = await self._repository.get_by_id(action.preset_id)

        # Validate labels against allowed filter_labels
        if preset_data.filter_labels:
            allowed = set(preset_data.filter_labels)
            invalid_labels = set(action.labels.keys()) - allowed
            if invalid_labels:
                raise InvalidAPIParameters(
                    f"Invalid filter labels: {sorted(invalid_labels)}. "
                    f"Allowed labels: {sorted(allowed)}"
                )

        # Validate group_labels against allowed group_labels
        if preset_data.group_labels:
            allowed_groups = set(preset_data.group_labels)
            invalid_groups = set(action.group_labels) - allowed_groups
            if invalid_groups:
                raise InvalidAPIParameters(
                    f"Invalid group labels: {sorted(invalid_groups)}. "
                    f"Allowed group labels: {sorted(allowed_groups)}"
                )

        # Window fallback chain: request window → preset time_window → server config
        window = action.window or preset_data.time_window or self._default_timewindow

        # Validate window format
        if not _WINDOW_PATTERN.match(window):
            raise InvalidAPIParameters(
                f"Invalid window format: '{window}'. Expected format: <number><unit> "
                f"where unit is one of s, m, h, d, w (e.g., '5m', '1h', '30s')"
            )

        metric_preset = MetricPreset(
            template=preset_data.query_template,
            labels=action.labels,
            group_by=set(action.group_labels),
            window=window,
        )

        response = await self._prometheus_client.query_range(
            preset=metric_preset,
            time_range=action.time_range,
        )

        return ExecutePresetActionResult(response=response)
