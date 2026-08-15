from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.services.prometheus_query_preset.actions.create import CreatePresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.execute_preset import (
    ExecutePresetAction,
    ExecutePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.get import GetPresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.preview import (
    PreviewPresetAction,
    PreviewPresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.purge import PurgePresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.search import SearchPresetsAction
from ai.backend.manager.services.prometheus_query_preset.actions.update import (
    UpdatePresetAction,
    UpdatePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


class PrometheusQueryPresetProcessors:
    """The catalog CRUD runs against ops; what reads before writing or calls Prometheus stays."""

    create_preset: GlobalActionProcessor[CreatePresetAction, CreatePresetActionResult]
    get_preset: GlobalActionProcessor[GetPresetAction, EntityOpsResult[PrometheusQueryPresetData]]
    search_presets: GlobalActionProcessor[
        SearchPresetsAction, BatchOpsResult[PrometheusQueryPresetData]
    ]
    purge_preset: GlobalActionProcessor[
        PurgePresetAction, EntityOpsResult[PrometheusQueryPresetData]
    ]
    update_preset: GlobalActionProcessor[UpdatePresetAction, UpdatePresetActionResult]
    preview_preset: GlobalActionProcessor[PreviewPresetAction, PreviewPresetActionResult]
    execute_preset: GlobalActionProcessor[ExecutePresetAction, ExecutePresetActionResult]

    def __init__(
        self,
        service: PrometheusQueryPresetService,
        group: ProcessorGroup[PrometheusQueryPresetData],
    ) -> None:
        # The create validates its query template, so it keeps a service method.
        self.create_preset = group.global_scope(CreatePresetAction, service.create_preset)
        self.get_preset = group.global_get_ops(GetPresetAction)
        self.search_presets = group.global_search_ops(SearchPresetsAction)
        self.purge_preset = group.global_purge_ops(PurgePresetAction)
        self.update_preset = group.global_scope(UpdatePresetAction, service.update_preset)
        self.preview_preset = group.global_scope(PreviewPresetAction, service.preview_preset)
        self.execute_preset = group.global_scope(ExecutePresetAction, service.execute_preset)
