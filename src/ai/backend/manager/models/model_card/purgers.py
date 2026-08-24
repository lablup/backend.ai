from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.model_card_resource_requirement import (
    ModelCardResourceRequirementID,
)
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot import ModelCardResourceRequirementRow
from ai.backend.manager.models.specs.purger import (
    EntityBatchPurger,
    EntityPurger,
    FieldBatchPurger,
)
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


@dataclass
class ModelCardResourceRequirementBatchPurger(
    FieldBatchPurger[ModelCardID, ModelCardResourceRequirementRow, ModelCardResourceRequirementID]
):
    """Clears the minimum slot quantities of one card, for the replacement to insert."""

    @override
    def build_subquery(
        self, owner_id: ModelCardID
    ) -> sa.sql.Select[tuple[ModelCardResourceRequirementRow]]:
        return sa.select(ModelCardResourceRequirementRow).where(
            ModelCardResourceRequirementRow.model_card_id == owner_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ModelCardResourceRequirementRow) -> ModelCardResourceRequirementID:
        return row.id


@dataclass
class ModelCardVFolderBatchPurger(EntityBatchPurger[ModelCardRow, ModelCardID]):
    """Clears every card registered on one vfolder, each with its graph.

    Used when a card delete takes its vfolder along: a sibling card left pointing
    at a trashed vfolder would be orphaned.
    """

    vfolder_id: VFolderUUID

    @override
    def entity_id(self, row: ModelCardRow) -> ModelCardID:
        return ModelCardID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[ModelCardRow]]:
        return sa.select(ModelCardRow).where(ModelCardRow.vfolder == self.vfolder_id)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardID:
        return ModelCardID(row.id)
