from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.scopes import ProjectModelCardOperationScope
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "ModelCardScopeItem",
    "ScopedSearchModelCardsAction",
)


@dataclass(frozen=True)
class ModelCardScopeItem(ScopeItem):
    """The model cards of one project."""

    project_id: ProjectID

    @override
    def scope_ref(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return ProjectModelCardOperationScope(project_id=self.project_id)


@dataclass(frozen=True)
class ScopedSearchModelCardsAction(OperationScopeOpsAction[ModelCardRow, ModelCardData]):
    """Page through the model cards the named scopes reach, combined with OR."""

    items: Sequence[ModelCardScopeItem]
    searcher: ModelCardSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ModelCardEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_model_cards"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_ref() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> ModelCardSearcher:
        return self.searcher
