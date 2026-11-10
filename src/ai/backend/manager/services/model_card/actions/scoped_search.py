from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow

__all__ = ("ScopedSearchModelCardsAction",)


@dataclass(frozen=True)
class ScopedSearchModelCardsAction(ScopedSearchOpsAction[ModelCardRow, ModelCardData]):
    """Page through the model cards the named scopes reach, combined with OR.

    Every scope is authorized and every using entity must be readable before the read
    runs, so a caller reaching for one they cannot see is refused rather than served the
    rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ModelCardEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_model_cards"
