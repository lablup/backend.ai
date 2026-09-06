from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.entity_label.scopes import EntityLabelOperationScope
from ai.backend.manager.models.entity_label.searchers import EntityLabelSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchEntityLabelsAction(BulkScopedSearchOpsAction[EntityLabelRow, EntityLabelData]):
    """Page through the labels on the entities named, combined with OR.

    Every entity is authorized before the read runs, so a label comes back exactly when
    its entity is readable and no rule of its own is needed.
    """

    owners: Sequence[EntityIdentifier]
    searcher: EntityLabelSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_entity_labels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return list(self.owners)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            EntityLabelOperationScope(entity_type=owner.entity_type(), entity_id=owner)
            for owner in self.owners
        ]

    @override
    def to_searcher(self) -> EntityLabelSearcher:
        return self.searcher
