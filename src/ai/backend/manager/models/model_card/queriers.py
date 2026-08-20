"""Query specs for the model cards table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.specs.querier import DataQuerier


@dataclass
class ModelCardQuerier(DataQuerier[ModelCardRow, ModelCardData]):
    """Reads one model card by its id."""

    model_card_id: ModelCardID

    @override
    def row_class(self) -> type[ModelCardRow]:
        return ModelCardRow

    @override
    def pk_value(self) -> UUID:
        return self.model_card_id

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()
