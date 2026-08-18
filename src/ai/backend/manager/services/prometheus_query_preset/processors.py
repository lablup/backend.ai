from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
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

    global_create_preset: GlobalActionProcessor[CreatePresetAction, CreatePresetActionResult]
    get_preset: SingleEntityActionProcessor[
        GetPresetAction, EntityOpsResult[PrometheusQueryPresetData]
    ]
    global_search_presets: GlobalActionProcessor[
        SearchPresetsAction, BatchOpsResult[PrometheusQueryPresetData]
    ]
    purge_preset: SingleEntityActionProcessor[
        PurgePresetAction, EntityOpsResult[PrometheusQueryPresetData]
    ]
    global_update_preset: GlobalActionProcessor[UpdatePresetAction, UpdatePresetActionResult]
    global_preview_preset: GlobalActionProcessor[PreviewPresetAction, PreviewPresetActionResult]
    global_execute_preset: GlobalActionProcessor[ExecutePresetAction, ExecutePresetActionResult]

    def __init__(
        self,
        service: PrometheusQueryPresetService,
        group: ProcessorGroup[PrometheusQueryPresetData],
    ) -> None:
            CreatePresetAction, service.create_preset
        self.global_search_presets = group.global_search_ops(SearchPresetsAction)
        self.purge_preset = group.entity_purge_ops(PurgePresetAction)
        self.global_update_preset = group.global_scope(UpdatePresetAction, service.update_preset)
        self.global_preview_preset = group.global_scope(PreviewPresetAction, service.preview_preset)
        self.global_execute_preset = group.global_scope(ExecutePresetAction, service.execute_preset)
