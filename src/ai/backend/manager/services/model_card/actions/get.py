from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.queriers import ModelCardQuerier
from ai.backend.manager.models.model_card.row import ModelCardRow


@dataclass(frozen=True)
class GetModelCardAction(GetSingleEntityOpsAction[ModelCardRow, ModelCardData]):
    """Read one model card by its id."""

    model_card_id: ModelCardID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.model_card_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_model_card"

    @override
    def to_querier(self) -> ModelCardQuerier:
        return ModelCardQuerier(model_card_id=self.model_card_id)
