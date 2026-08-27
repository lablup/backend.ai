from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, PROJECT_SCOPE_TYPE, ProjectID
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.scopes import ProjectModelCardOperationScope
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass(frozen=True)
class SearchModelCardsInProjectAction(OperationScopeOpsAction[ModelCardRow, ModelCardData]):
    """Page through the model cards of a MODEL_STORE project."""

    project_id: ProjectID
    searcher: ModelCardSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=PROJECT_SCOPE_TYPE, scope_id=self.project_id),)

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (PROJECT_ENTITY_TYPE,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (ProjectModelCardOperationScope(project_id=self.project_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_model_cards_in_project"

    @override
    def to_searcher(self) -> ModelCardSearcher:
        return self.searcher
