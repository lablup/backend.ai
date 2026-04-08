from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.model_card.types import ProjectModelCardSearchScope
from ai.backend.manager.services.model_card.actions.base import ModelCardScopeAction


@dataclass
class SearchModelCardsInProjectAction(ModelCardScopeAction):
    """Search model cards within a MODEL_STORE project scope."""

    scope: ProjectModelCardSearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.PROJECT

    @override
    def scope_id(self) -> str:
        return str(self.scope.project_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(
            element_type=RBACElementType.PROJECT,
            element_id=str(self.scope.project_id),
        )


@dataclass
class SearchModelCardsInProjectActionResult(BaseActionResult):
    items: list[ModelCardData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
