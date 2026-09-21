"""Searcher implementations for the deployment revision preset repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.deployment_revision_preset.searchable_fields import (
    DeploymentPresetSearchableFields,
)
from ai.backend.manager.models.resource_slot.row import (
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_slot.searchable_fields import (
    PresetResourceSlotSearchableFields,
)
from ai.backend.manager.models.specs.pagination import QueryPagination
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = (
    "DeploymentPresetSearcher",
    "ModelCardSatisfyingPresetSearcher",
    "PresetResourceSlotSearcher",
)


@dataclass
class DeploymentPresetSearcher(Searcher[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentRevisionPresetRow)

    @override
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return DeploymentPresetSearchableFields.own.to_data(row)


class ModelCardSatisfyingPresetSearcher(DeploymentPresetSearcher):
    """The presets meeting every minimum slot quantity a model card requires.

    Relational division: a preset qualifies iff no required slot lacks a slot row whose
    quantity meets the minimum. Both EXISTS clauses correlate against the outer preset
    (and the outer requirement), without which SQLAlchemy aliases the inner FROM and the
    predicates degenerate into Cartesian matches that accept every preset.
    """

    def __init__(self, model_card_id: ModelCardID, pagination: QueryPagination) -> None:
        super().__init__(pagination=pagination, conditions=[self._satisfying(model_card_id)])

    def _satisfying(self, model_card_id: ModelCardID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            preset = DeploymentRevisionPresetRow.__table__
            requirement = ModelCardResourceRequirementRow.__table__
            slot = PresetResourceSlotRow.__table__
            return ~sa.exists(
                sa.select(sa.literal(1))
                .select_from(requirement)
                .correlate(preset)
                .where(
                    requirement.c.model_card_id == model_card_id,
                    ~sa.exists(
                        sa.select(sa.literal(1))
                        .select_from(slot)
                        .correlate(preset, requirement)
                        .where(
                            slot.c.preset_id == preset.c.id,
                            slot.c.slot_name == requirement.c.slot_name,
                            slot.c.quantity >= requirement.c.min_quantity,
                        )
                    ),
                )
            )

        return inner


@dataclass
class PresetResourceSlotSearcher(Searcher[PresetResourceSlotRow, PresetResourceSlotData]):
    """Slot rows in the slot catalog's own rank order.

    The order is built in rather than left to the caller: a slot list shown in any
    other order would disagree with every other place slots appear. Which preset's
    rows these are is the operation scope's to say.
    """

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(PresetResourceSlotRow)
            .join(
                ResourceSlotTypeRow,
                PresetResourceSlotRow.slot_name == ResourceSlotTypeRow.slot_name,
            )
            .order_by(ResourceSlotTypeRow.rank)
        )

    @override
    def to_data(self, row: PresetResourceSlotRow) -> PresetResourceSlotData:
        return PresetResourceSlotSearchableFields.own.to_data(row)
