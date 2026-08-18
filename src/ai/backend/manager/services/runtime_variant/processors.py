from __future__ import annotations

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import (
    PublicSingleEntityActionProcessor,
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.services.runtime_variant.actions.create import (
    CreateRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.get import GetRuntimeVariantAction
from ai.backend.manager.services.runtime_variant.actions.lookup import (
    LookupRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.purge import (
    PurgeRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.search import (
    SearchRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.update import (
    UpdateRuntimeVariantAction,
)


class RuntimeVariantProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    public_get: PublicSingleEntityActionProcessor[
        GetRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]
    ]
    global_create: GlobalActionProcessor[
        CreateRuntimeVariantAction, CreatedEntityOpsResult[RuntimeVariantData]
    ]
    update: SingleEntityActionProcessor[
        UpdateRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]
    ]
    public_search: PublicActionProcessor[
        SearchRuntimeVariantsAction, BatchOpsResult[RuntimeVariantData]
    ]
    public_lookup: LookupActionProcessor[
        LookupRuntimeVariantAction, LookupOpsResult[RuntimeVariantData]
    ]

    def __init__(self, group: ProcessorGroup[RuntimeVariantData]) -> None:
        self.public_get = group.public_get_ops(GetRuntimeVariantAction)
        self.global_create = group.global_create_ops(CreateRuntimeVariantAction)
        self.update = group.single_update_ops(UpdateRuntimeVariantAction)
        self.purge = group.entity_purge_ops(PurgeRuntimeVariantAction)
        self.public_search = group.public_search_ops(SearchRuntimeVariantsAction)
        self.public_lookup = group.public_lookup_ops(LookupRuntimeVariantAction)
