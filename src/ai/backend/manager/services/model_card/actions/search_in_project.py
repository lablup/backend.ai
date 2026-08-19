from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.model_card.types import ProjectModelCardOperationScope
from ai.backend.manager.services.model_card.actions.base import ModelCardScopeAction


@dataclass
class SearchModelCardsInProjectAction(ModelCardScopeAction):
    """Search model cards within a MODEL_STORE project scope."""

    scope: ProjectModelCardOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_model_cards_in_project"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchModelCardsInProjectActionResult:
    items: list[ModelCardData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
