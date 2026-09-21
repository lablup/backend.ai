from __future__ import annotations

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.services.runtime_variant.actions.bulk_get import (
    BulkGetRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.bulk_purge import (
    BulkPurgeRuntimeVariantsAction,
)
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
from ai.backend.manager.services.runtime_variant.actions.scoped_search import (
    ScopedSearchRuntimeVariantsAction,
)
from ai.backend.manager.services.runtime_variant.actions.update import (
    UpdateRuntimeVariantAction,
)
from ai.backend.manager.services.runtime_variant.service import RuntimeVariantService


class RuntimeVariantProcessors:
    """Every operation but the purges runs straight against ops; the purges clear presets."""

    get: SingleEntityActionProcessor[GetRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]]
    bulk_get: PartialBulkActionProcessor[BulkGetRuntimeVariantsAction, RuntimeVariantData]
    global_create: GlobalActionProcessor[
        CreateRuntimeVariantAction, CreatedEntityOpsResult[RuntimeVariantData]
    ]
    update: SingleEntityActionProcessor[
        UpdateRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]
    ]
    purge: SingleEntityActionProcessor[
        PurgeRuntimeVariantAction, EntityOpsResult[RuntimeVariantData]
    ]
    bulk_purge: PartialBulkActionProcessor[BulkPurgeRuntimeVariantsAction, RuntimeVariantData]
    scoped_search: ScopeActionProcessor[
        ScopedSearchRuntimeVariantsAction, ScopedBatchOpsResult[RuntimeVariantData]
    ]
    lookup: LookupActionProcessor[LookupRuntimeVariantAction, LookupOpsResult[RuntimeVariantID]]

    def __init__(
        self, group: ProcessorGroup[RuntimeVariantData], service: RuntimeVariantService
    ) -> None:
        self.get = group.single_get_ops(GetRuntimeVariantAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetRuntimeVariantsAction)
        self.global_create = group.global_create_ops(CreateRuntimeVariantAction)
        self.update = group.single_update_ops(UpdateRuntimeVariantAction)
        self.purge = group.single_entity(PurgeRuntimeVariantAction, service.purge)
        self.bulk_purge = group.partial_bulk(BulkPurgeRuntimeVariantsAction, service.bulk_purge)
        self.scoped_search = group.scoped_search_ops(ScopedSearchRuntimeVariantsAction)
        self.lookup = group.lookup_ops(LookupRuntimeVariantAction)
