from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, EntityOpsResult
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
    CreateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.actions.get import (
    GetRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.purge import (
    PurgeRuntimeVariantPresetAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.search import (
    SearchRuntimeVariantPresetsAction,
)
from ai.backend.manager.services.runtime_variant_preset.actions.update import (
    UpdateRuntimeVariantPresetAction,
    UpdateRuntimeVariantPresetActionResult,
)
from ai.backend.manager.services.runtime_variant_preset.service import (
    RuntimeVariantPresetService,
)


class RuntimeVariantPresetProcessors:
    """Reads and the removal run against ops; the two writes keep their service."""

    public_get: PublicSingleEntityActionProcessor[
        GetRuntimeVariantPresetAction, EntityOpsResult[RuntimeVariantPresetData]
    ]
    global_create: GlobalActionProcessor[
        CreateRuntimeVariantPresetAction, CreateRuntimeVariantPresetActionResult
    ]
    global_update: GlobalActionProcessor[
        UpdateRuntimeVariantPresetAction, UpdateRuntimeVariantPresetActionResult
    ]
    global_purge: GlobalActionProcessor[
        PurgeRuntimeVariantPresetAction, EntityOpsResult[RuntimeVariantPresetData]
    ]
    public_search: PublicActionProcessor[
        SearchRuntimeVariantPresetsAction, BatchOpsResult[RuntimeVariantPresetData]
    ]

    def __init__(
        self,
        service: RuntimeVariantPresetService,
        group: ProcessorGroup[RuntimeVariantPresetData],
    ) -> None:
        self.public_get = group.public_get_ops(GetRuntimeVariantPresetAction)
        self.global_create = group.global_scope(CreateRuntimeVariantPresetAction, service.create)
        self.global_update = group.global_scope(UpdateRuntimeVariantPresetAction, service.update)
        self.global_purge = group.global_purge_ops(PurgeRuntimeVariantPresetAction)
        self.public_search = group.public_search_ops(SearchRuntimeVariantPresetsAction)
