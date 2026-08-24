from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedFieldOpsResult,
    EntityOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.services.label.actions.add import AddLabelAction
from ai.backend.manager.services.label.actions.remove import RemoveLabelAction
from ai.backend.manager.services.label.actions.search import SearchLabelsAction


class LabelProcessors:
    """The three operations over labels, all straight against ops.

    A label is a field of the entity it is on, so each of these is answered for by that
    entity: the add names it as its target, the removal reads it from the row it names,
    and the search names the entities whose labels it returns. Which kind of entity is
    not fixed, which is why the group is reached from the registry rather than from an
    entity's own group.
    """

    add: SingleEntityActionProcessor[AddLabelAction, CreatedFieldOpsResult[LabelData]]
    remove: SingleFieldActionProcessor[RemoveLabelAction, EntityOpsResult[LabelData]]
    search: BulkActionProcessor[SearchLabelsAction, ScopedFieldsOpsResult[LabelData]]

    def __init__(self, group: LookupFieldGroup[LabelData]) -> None:
        self.add = group.create_ops(AddLabelAction)
        self.remove = group.purge_ops(RemoveLabelAction)
        self.search = group.atomic_bulk_scoped_search_ops(SearchLabelsAction)
