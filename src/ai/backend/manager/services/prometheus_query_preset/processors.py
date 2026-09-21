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
from ai.backend.manager.services.prometheus_query_preset.actions.bulk_get import (
    PublicBulkGetPresetsAction,
)
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
    public_bulk_get_presets: PartialBulkActionProcessor[
        PublicBulkGetPresetsAction, PrometheusQueryPresetData
    ]
    scoped_search_presets: ScopeActionProcessor[
        ScopedSearchPresetsAction, ScopedBatchOpsResult[PrometheusQueryPresetData]
    ]
    purge_preset: SingleEntityActionProcessor[
        PurgePresetAction, EntityOpsResult[PrometheusQueryPresetData]
    ]
    update_preset: SingleEntityActionProcessor[UpdatePresetAction, UpdatePresetActionResult]
    global_preview_preset: GlobalActionProcessor[PreviewPresetAction, PreviewPresetActionResult]
    execute_preset: SingleEntityActionProcessor[ExecutePresetAction, ExecutePresetActionResult]

    def __init__(
        self,
        group: ProcessorGroup[PrometheusQueryPresetData],
        service: PrometheusQueryPresetService,
    ) -> None:
        # The create validates its query template, so it keeps a service method.
        self.global_create_preset = group.global_scope(CreatePresetAction, service.create_preset)
        self.get_preset = group.single_get_ops(GetPresetAction)
        self.public_bulk_get_presets = group.public_partial_bulk_get_ops(PublicBulkGetPresetsAction)
        self.scoped_search_presets = group.scoped_search_ops(ScopedSearchPresetsAction)
        self.purge_preset = group.entity_purge_ops(PurgePresetAction)
        self.update_preset = group.single_entity(UpdatePresetAction, service.update_preset)
        self.global_preview_preset = group.global_scope(PreviewPresetAction, service.preview_preset)
        self.execute_preset = group.single_entity(ExecutePresetAction, service.execute_preset)
