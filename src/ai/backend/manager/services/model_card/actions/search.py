from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.searchers import ModelCardSearcher


@dataclass(frozen=True)
class GlobalSearchModelCardsAction(SearchGlobalOpsAction[ModelCardRow, ModelCardData]):
    """Page through every model card in the installation."""

    searcher: ModelCardSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_model_cards"

    @override
    def to_searcher(self) -> ModelCardSearcher:
        return self.searcher
