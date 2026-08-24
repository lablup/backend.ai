from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.label.scopes import EntityLabelOperationScope
from ai.backend.manager.models.label.searchers import LabelSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchLabelsAction(BulkScopedSearchOpsAction[LabelRow, LabelData]):
    """Page through the labels on the entities named, combined with OR.

    Every entity is authorized before the read runs, so a label comes back exactly when
    its entity is readable and no rule of its own is needed.
    """

    owners: Sequence[EntityIdentifier]
    searcher: LabelSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_labels"

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
    def to_searcher(self) -> LabelSearcher:
        return self.searcher
