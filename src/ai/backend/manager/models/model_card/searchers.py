"""Searcher specs for the model cards table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ModelCardSearcher(Searcher[ModelCardRow, ModelCardData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ModelCardRow)

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()


@dataclass
class ModelCardResourceRequirementSearcher(
    Searcher[ModelCardResourceRequirementRow, ModelCardResourceRequirementData]
):
    """Minimum quantity rows in the slot catalog's own rank order.

    The order is built in rather than left to the caller: a slot list shown in any
    other order would disagree with every other place slots appear. Which cards'
    rows these are is the operation scope's to say.
    """

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(ModelCardResourceRequirementRow)
            .join(
                ResourceSlotTypeRow,
                ModelCardResourceRequirementRow.slot_name == ResourceSlotTypeRow.slot_name,
            )
            .order_by(ResourceSlotTypeRow.rank)
        )

    @override
    def to_data(self, row: ModelCardResourceRequirementRow) -> ModelCardResourceRequirementData:
        return row.to_data()
