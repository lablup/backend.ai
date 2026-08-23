from __future__ import annotations

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.services.runtime_variant_preset.actions.create import (
    CreateRuntimeVariantPresetAction,
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
    """Everything but the update runs against ops; the update reads before it writes."""

    public_get: PublicSingleEntityActionProcessor[
        GetRuntimeVariantPresetAction, EntityOpsResult[RuntimeVariantPresetData]
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
    public_search: PublicActionProcessor[
        SearchRuntimeVariantPresetsAction, BatchOpsResult[RuntimeVariantPresetData]
    ]

    def __init__(
        self,
        group: ProcessorGroup[RuntimeVariantPresetData],
        service: RuntimeVariantPresetService,
    ) -> None:
        self.public_get = group.public_get_ops(GetRuntimeVariantPresetAction)
        self.global_create = group.global_create_ops(CreateRuntimeVariantPresetAction)
        self.update = group.single_entity(UpdateRuntimeVariantPresetAction, service.update)
        self.purge = group.entity_purge_ops(PurgeRuntimeVariantPresetAction)
        self.public_search = group.public_search_ops(SearchRuntimeVariantPresetsAction)
