from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ModelCardPurger(EntityPurger[ModelCardRow, ModelCardData]):
    """Purger for removing a model card."""

    card_id: ModelCardID

    @override
    def entity_id(self) -> ModelCardID:
        return self.card_id

    @override
    def row_class(self) -> type[ModelCardRow]:
        return ModelCardRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ModelCardRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()
