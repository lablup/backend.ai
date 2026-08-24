"""Read specs resolving a model card's field rows into the card that owns them."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.model_card_resource_requirement import (
    ModelCardResourceRequirementID,
)
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup

__all__ = ("ModelCardResourceRequirementOwnerLookup",)


class ModelCardResourceRequirementOwnerLookup(
    FieldOwnerLookup[ModelCardResourceRequirementID, ModelCardID]
):
    """The card a minimum-quantity row belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[ModelCardResourceRequirementID]
    ) -> sa.sql.Select[Any]:
        return sa.select(
            ModelCardResourceRequirementRow.id,
            ModelCardResourceRequirementRow.model_card_id,
        ).where(ModelCardResourceRequirementRow.id.in_(field_ids))

    @override
    def to_entity_id(self, row: Row[Any]) -> ModelCardID:
        return ModelCardID(row[1])
