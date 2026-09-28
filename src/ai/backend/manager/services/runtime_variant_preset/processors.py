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
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.services.runtime_variant_preset.actions.bulk_get import (
    BulkGetRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.get import (
    GetRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.purge import (
    PurgeRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.scoped_search import (
    ScopedSearchRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.service import (
    RuntimeVariantPresetService,
)


class RuntimeVariantPresetProcessors:
    """Everything but the update runs against ops; the update reads before it writes."""

    get: SingleEntityActionProcessor[
        GetRuntimeVariantPresetAction, EntityOpsResult[RuntimeVariantPresetData]
    ]
    bulk_get: PartialBulkActionProcessor[
        BulkGetRuntimeVariantPresetsAction, RuntimeVariantPresetData
    ]
    global_create: GlobalActionProcessor[
        CreateRuntimeVariantPresetAction, CreatedEntityOpsResult[RuntimeVariantPresetData]
    ]
    update: SingleEntityActionProcessor[
        UpdateRuntimeVariantPresetAction, UpdateRuntimeVariantPresetActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeRuntimeVariantPresetAction, EntityOpsResult[RuntimeVariantPresetData]
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchRuntimeVariantPresetsAction, ScopedBatchOpsResult[RuntimeVariantPresetData]
    ]

    def __init__(
        self,
        group: ProcessorGroup[RuntimeVariantPresetData],
        service: RuntimeVariantPresetService,
    ) -> None:
        self.get = group.single_get_ops(GetRuntimeVariantPresetAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetRuntimeVariantPresetsAction)
        self.global_create = group.global_create_ops(CreateRuntimeVariantPresetAction)
        self.update = group.single_entity(UpdateRuntimeVariantPresetAction, service.update)
        self.purge = group.entity_purge_ops(PurgeRuntimeVariantPresetAction)
        self.scoped_search = group.scoped_search_ops(ScopedSearchRuntimeVariantPresetsAction)
