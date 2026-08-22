"""Read of the minimum quantities the named cards declare."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.model_card.types import ModelCardResourceRequirementData
from ai.backend.manager.models.model_card.searchers import (
    ModelCardResourceRequirementSearcher,
)
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.scopes import OperationScope
from ai.backend.manager.repositories.model_card.types import (
    ModelCardResourceRequirementOperationScope,
)


@dataclass
class ScopedSearchModelCardResourceRequirementsAction(
    BulkScopedSearchOpsAction[ModelCardResourceRequirementRow, ModelCardResourceRequirementData]
):
    """Read the requirement rows of the cards named, combined with OR.

    Every card is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    card_ids: Sequence[ModelCardID]
    searcher: ModelCardResourceRequirementSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_model_card_resource_requirements"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.card_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [
            ModelCardResourceRequirementOperationScope(model_card_id=card_id)
            for card_id in self.card_ids
        ]

    @override
    def to_searcher(self) -> ModelCardResourceRequirementSearcher:
        return self.searcher
