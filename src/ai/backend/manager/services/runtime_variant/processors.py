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
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.services.runtime_variant.actions.create import (
    CreateRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.purge import (
    PurgeRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.actions.resolve_by_name import (
    ResolveRuntimeVariantByNameAction,
)
from ai.backend.manager.services.runtime_variant.actions.search import (
    SearchRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.update import (
    UpdateRuntimeVariantAction,
)


class RuntimeVariantProcessors:
    """Every operation runs straight against ops, so this domain has no service."""

    create: GlobalActionProcessor[
        CreateRuntimeVariantAction, CreatedEntityOpsResult[RuntimeVariantData]
    ]
    update: GlobalActionProcessor[UpdateRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]]
    purge: GlobalActionProcessor[PurgeRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]]
    search: PublicActionProcessor[SearchRuntimeVariantsAction, BatchOpsResult[RuntimeVariantData]]
    lookup: LookupActionProcessor[
        ResolveRuntimeVariantByNameAction, LookupOpsResult[RuntimeVariantData]
    ]

    def __init__(self, group: ProcessorGroup[RuntimeVariantData]) -> None:
        self.create = group.global_create_ops(CreateRuntimeVariantAction)
        self.update = group.global_update_ops(UpdateRuntimeVariantAction)
        self.purge = group.global_purge_ops(PurgeRuntimeVariantAction)
        self.search = group.public_search_ops(SearchRuntimeVariantsAction)
        self.lookup = group.lookup_ops(ResolveRuntimeVariantByNameAction)
