from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.queriers import BulkModelCardQuerier
from ai.backend.manager.models.model_card.row import ModelCardRow


@dataclass(frozen=True)
class BulkGetModelCardsAction(PartialBulkGetEntityOpsAction[ModelCardRow, ModelCardData]):
    """Read the model cards the caller named, one permission check per card."""

    ids: Sequence[ModelCardID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_model_cards"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkModelCardQuerier:
        return BulkModelCardQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
