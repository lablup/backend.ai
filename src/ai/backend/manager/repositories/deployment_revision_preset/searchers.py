"""Searcher implementations for the deployment revision preset repository."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow, ResourceSlotTypeRow
from ai.backend.manager.models.specs.searcher import Searcher

__all__ = (
    "DeploymentPresetSearcher",
    "PresetResourceSlotSearcher",
)


@dataclass
class DeploymentPresetSearcher(Searcher[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(DeploymentRevisionPresetRow)

    @override
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return row.to_data()


@dataclass
class PresetResourceSlotSearcher(Searcher[PresetResourceSlotRow, PresetResourceSlotData]):
    """One preset's slot rows, in the slot catalog's own rank order.

    The order is built in rather than left to the caller: a slot list shown in any
    other order would disagree with every other place slots appear.
    """

    preset_id: DeploymentPresetID = field(default=None)  # type: ignore[assignment]

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return (
            sa.select(PresetResourceSlotRow)
            .join(
                ResourceSlotTypeRow,
                PresetResourceSlotRow.slot_name == ResourceSlotTypeRow.slot_name,
            )
            .where(PresetResourceSlotRow.preset_id == self.preset_id)
            .order_by(ResourceSlotTypeRow.rank)
        )

    @override
    def to_data(self, row: PresetResourceSlotRow) -> PresetResourceSlotData:
        return PresetResourceSlotData(
            preset_id=DeploymentPresetID(row.preset_id),
            slot_name=row.slot_name,
            quantity=row.quantity,
        )
