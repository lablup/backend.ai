from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import final, override

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.scopes import ModelCardTarget
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = ("ScopedSearchModelCardsAction",)


@dataclass(frozen=True)
class ScopedSearchModelCardsAction(OperationScopeOpsAction[ModelCardRow, ModelCardData]):
    """Page through the model cards the named scopes reach, combined with OR."""

    targets: Sequence[ModelCardTarget]
    searcher: ModelCardSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ModelCardEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_model_cards"

    @final
    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [target.scope_id() for target in self.targets]

    @final
    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return self.targets

    @override
    def to_searcher(self) -> ModelCardSearcher:
        return self.searcher
