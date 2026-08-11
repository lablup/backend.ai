from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.ops.result import BatchOpsResult, EntityOpsResult
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
    CreateRuntimeVariantPresetActionResult,
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

    create: GlobalActionProcessor[
        CreateRuntimeVariantPresetAction, CreateRuntimeVariantPresetActionResult
    ]
    update: GlobalActionProcessor[
        UpdateRuntimeVariantPresetAction, UpdateRuntimeVariantPresetActionResult
    ]
    purge: GlobalActionProcessor[
        PurgeRuntimeVariantPresetAction, EntityOpsResult[RuntimeVariantPresetData]
    ]
    search: GlobalActionProcessor[
        SearchRuntimeVariantPresetsAction, BatchOpsResult[RuntimeVariantPresetData]
    ]

    def __init__(
        self,
        service: RuntimeVariantPresetService,
        group: ProcessorGroup[RuntimeVariantPresetData],
    ) -> None:
        self.create = group.global_scope(CreateRuntimeVariantPresetAction, service.create)
        self.update = group.global_scope(UpdateRuntimeVariantPresetAction, service.update)
        self.purge = group.global_purge_ops(PurgeRuntimeVariantPresetAction)
        self.search = group.global_search_ops(SearchRuntimeVariantPresetsAction)
