from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    EntityOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.services.entity_label.actions.partial_bulk_get import (
    PartialBulkGetEntityLabelAction,
)
from ai.backend.manager.services.entity_label.actions.partial_bulk_purge import (
    PartialBulkPurgeEntityLabelAction,
)
from ai.backend.manager.services.entity_label.actions.partial_bulk_upsert import (
    PartialBulkUpsertEntityLabelAction,
)
from ai.backend.manager.services.entity_label.actions.purge import PurgeEntityLabelAction
from ai.backend.manager.services.entity_label.actions.search import SearchEntityLabelsAction
from ai.backend.manager.services.entity_label.actions.upsert import UpsertEntityLabelAction


class EntityLabelProcessors:
    """The operations over labels, all straight against ops and each answered for by
    the labeled entity. Its kind is a value on the row, which is why the group comes
    from the registry rather than an entity's own group."""

    upsert: SingleEntityActionProcessor[UpsertEntityLabelAction, EntityOpsResult[EntityLabelData]]
    partial_bulk_upsert: PartialBulkActionProcessor[
        PartialBulkUpsertEntityLabelAction, list[EntityLabelData]
    ]
    purge: SingleFieldActionProcessor[PurgeEntityLabelAction, EntityOpsResult[EntityLabelData]]
    partial_bulk_purge: PartialBulkFieldActionProcessor[
        PartialBulkPurgeEntityLabelAction, EntityLabelData
    ]
    search: BulkActionProcessor[SearchEntityLabelsAction, ScopedFieldsOpsResult[EntityLabelData]]
    partial_bulk_get: PartialBulkFieldActionProcessor[
        PartialBulkGetEntityLabelAction, EntityLabelData
    ]

    def __init__(self, group: LookupFieldGroup[EntityLabelData]) -> None:
        self.upsert = group.upsert_ops(UpsertEntityLabelAction)
        self.partial_bulk_upsert = group.partial_bulk_upsert_ops(PartialBulkUpsertEntityLabelAction)
        self.purge = group.runtime_purge_ops(PurgeEntityLabelAction)
        self.partial_bulk_purge = group.partial_bulk_purge_ops(PartialBulkPurgeEntityLabelAction)
        self.search = group.atomic_bulk_scoped_search_ops(SearchEntityLabelsAction)
        self.partial_bulk_get = group.partial_bulk_get_ops(PartialBulkGetEntityLabelAction)
