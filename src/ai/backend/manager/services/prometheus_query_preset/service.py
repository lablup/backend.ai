import logging
from typing import cast

from ai.backend.common.exception import PrometheusQueryPresetInvalidLabel
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.v2.ops.result import CreatedEntityOpsResult
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.clients.prometheus.preset import (
    LabelMatcher,
    MetricPreset,
    PromQLTemplateRenderer,
)
from ai.backend.manager.data.prometheus_query_preset import (
    ExecutePresetOptions,
    PrometheusQueryPresetData,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.services.prometheus_query_preset.actions import (
    CreatePresetAction,
    ExecutePresetAction,
    ExecutePresetActionResult,
    PreviewPresetAction,
    PreviewPresetActionResult,
    UpdatePresetAction,
    UpdatePresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class PrometheusQueryPresetService:
    _repository: PrometheusQueryPresetRepository
    _prometheus_client: PrometheusClient
    _default_timewindow: str
    _template_renderer: PromQLTemplateRenderer
    _ops_repository: OpsRepository[PrometheusQueryPresetData]

    def __init__(
        self,
        repository: PrometheusQueryPresetRepository,
        prometheus_client: PrometheusClient,
        default_timewindow: str,
        template_renderer: PromQLTemplateRenderer,
        ops_repository: OpsRepository[PrometheusQueryPresetData],
    ) -> None:
        self._repository = repository
        self._prometheus_client = prometheus_client
        self._default_timewindow = default_timewindow
        self._template_renderer = template_renderer
        self._ops_repository = ops_repository

    async def create_preset(
        self, action: CreatePresetAction
    ) -> CreatedEntityOpsResult[PrometheusQueryPresetData]:
        self._template_renderer.validate(action.creator.query_template)
        return CreatedEntityOpsResult(
            data=await self._ops_repository.create_global_entity(action.to_creator())
        )

    async def update_preset(self, action: UpdatePresetAction) -> UpdatePresetActionResult:
        spec = cast(PrometheusQueryPresetUpdaterSpec, action.updater.spec)
        template = spec.query_template.optional_value()
        if template is not None:
            self._template_renderer.validate(template)
        preset_data = await self._repository.update(action.updater)
        return UpdatePresetActionResult(preset=preset_data)

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

    async def preview_preset(self, action: PreviewPresetAction) -> PreviewPresetActionResult:
        self._template_renderer.validate(action.query_template)
        response = await self._repository.preview_template(
            query_template=action.query_template,
            default_window=self._default_timewindow,
        )
        return PreviewPresetActionResult(response=response)

    async def execute_preset(self, action: ExecutePresetAction) -> ExecutePresetActionResult:
        preset_data = await self._repository.get_by_id(action.preset_id)
        self._validate_labels(action.options, preset_data)
        # Window fallback: request → preset → server default
        time_window = action.time_window or preset_data.time_window or self._default_timewindow

        response = await self._prometheus_client.execute_preset(
            MetricPreset(
                template=preset_data.query_template,
                labels={
                    name: LabelMatcher.exact(value)
                    for name, value in action.options.filter_labels.items()
                },
                group_by=set(action.options.group_labels),
                window=time_window,
            ),
            time_range=action.time_range,
        )
        return ExecutePresetActionResult(response=response)
