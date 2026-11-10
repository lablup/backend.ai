from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntityOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.prometheus_query_preset.types import PrometheusQueryPresetData
from ai.backend.manager.services.prometheus_query_preset.actions.create import CreatePresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.execute_preset import (
    ExecutePresetAction,
    ExecutePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.get import GetPresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.partial_bulk_purge import (
    PartialBulkPurgePresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.partial_bulk_update import (
    PartialBulkUpdatePresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.preview import (
    PreviewPresetAction,
    PreviewPresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.actions.purge import PurgePresetAction
from ai.backend.manager.services.prometheus_query_preset.actions.scoped_search import (
    ScopedSearchPresetsAction,
)
from ai.backend.manager.services.prometheus_query_preset.actions.update import (
    UpdatePresetAction,
    UpdatePresetActionResult,
)
from ai.backend.manager.services.prometheus_query_preset.service import (
    PrometheusQueryPresetService,
)


class PrometheusQueryPresetProcessors:
    """The catalog CRUD runs against ops; what reads before writing or calls Prometheus stays."""

    global_create_preset: GlobalActionProcessor[
        CreatePresetAction, CreatedEntityOpsResult[PrometheusQueryPresetData]
    ]
    get_preset: SingleEntityActionProcessor[
        GetPresetAction, EntityOpsResult[PrometheusQueryPresetData]
    ]
    scoped_search_presets: ScopeActionProcessor[
        ScopedSearchPresetsAction, ScopedBatchOpsResult[PrometheusQueryPresetData]
    ]
    purge_preset: SingleEntityActionProcessor[
        PurgePresetAction, EntityOpsResult[PrometheusQueryPresetData]
    ]
    update_preset: SingleEntityActionProcessor[UpdatePresetAction, UpdatePresetActionResult]
    partial_bulk_update_presets: PartialBulkActionProcessor[
        PartialBulkUpdatePresetsAction, PrometheusQueryPresetData
    ]
    partial_bulk_purge_presets: PartialBulkActionProcessor[
        PartialBulkPurgePresetsAction, PrometheusQueryPresetData
    ]
    global_preview_preset: GlobalActionProcessor[PreviewPresetAction, PreviewPresetActionResult]
    execute_preset: SingleEntityActionProcessor[ExecutePresetAction, ExecutePresetActionResult]

    def __init__(
        self,
        group: ProcessorGroup[PrometheusQueryPresetData],
        service: PrometheusQueryPresetService,
    ) -> None:
        # The create and the updates validate their query template, so they keep a service method.
        self.global_create_preset = group.global_scope(CreatePresetAction, service.create_preset)
        self.get_preset = group.single_get_ops(GetPresetAction)
        self.scoped_search_presets = group.scoped_search_ops(ScopedSearchPresetsAction)
        self.purge_preset = group.entity_purge_ops(PurgePresetAction)
        self.update_preset = group.single_entity(UpdatePresetAction, service.update_preset)
        self.partial_bulk_update_presets = group.partial_bulk(
            PartialBulkUpdatePresetsAction, service.partial_bulk_update_presets
        )
        self.partial_bulk_purge_presets = group.entity_partial_bulk_purge_ops(
            PartialBulkPurgePresetsAction
        )
        self.global_preview_preset = group.global_scope(PreviewPresetAction, service.preview_preset)
        self.execute_preset = group.single_entity(ExecutePresetAction, service.execute_preset)
