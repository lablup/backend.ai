from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    EntityOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.services.entity_label.actions.put import PutEntityLabelAction
from ai.backend.manager.services.entity_label.actions.remove import RemoveEntityLabelAction
from ai.backend.manager.services.entity_label.actions.search import SearchEntityLabelsAction


class EntityLabelProcessors:
    """The three operations over labels, all straight against ops.

    A label is a field of the entity it is on, so each of these is answered for by that
    entity: the put names it as its target, the removal reads it from the row it names,
    and the search names the entities whose labels it returns. Which kind of entity is
    not fixed, which is why the group is reached from the registry rather than from an
    entity's own group.
    """

    put: SingleEntityActionProcessor[PutEntityLabelAction, EntityOpsResult[EntityLabelData]]
    remove: SingleFieldActionProcessor[RemoveEntityLabelAction, EntityOpsResult[EntityLabelData]]
    search: BulkActionProcessor[SearchEntityLabelsAction, ScopedFieldsOpsResult[EntityLabelData]]

    def __init__(self, group: LookupFieldGroup[EntityLabelData]) -> None:
        self.put = group.upsert_ops(PutEntityLabelAction)
        self.remove = group.runtime_purge_ops(RemoveEntityLabelAction)
        self.search = group.atomic_bulk_scoped_search_ops(SearchEntityLabelsAction)
