from __future__ import annotations

from collections.abc import Sequence
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.manager.data.deployment_revision_preset.types import (
    DeploymentRevisionPresetData,
    ResourceSlotEntryData,
)
from ai.backend.manager.models.deployment_revision_preset.row import DeploymentRevisionPresetRow
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.specs.purger import DataBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck

__all__ = (
    "DeploymentPresetPurger",
    "PresetResourceSlotBatchPurger",
)


class DeploymentPresetPurger(
    EntityPurger[DeploymentRevisionPresetRow, DeploymentRevisionPresetData]
):
    """Remove a preset. Its slot rows go with it by FK cascade."""

    _preset_id: DeploymentPresetID

    def __init__(self, preset_id: DeploymentPresetID) -> None:
        self._preset_id = preset_id

    @override
    def entity_id(self) -> DeploymentPresetID:
        return self._preset_id

    @override
    def row_class(self) -> type[DeploymentRevisionPresetRow]:
        return DeploymentRevisionPresetRow

    @override
    def pk_value(self) -> DeploymentPresetID:
        return self._preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: DeploymentRevisionPresetRow) -> DeploymentRevisionPresetData:
        return row.to_data()


class PresetResourceSlotBatchPurger(DataBatchPurger[PresetResourceSlotRow, ResourceSlotEntryData]):
    """Clear every slot row of one preset, so an update can restate the whole set."""

    _preset_id: DeploymentPresetID

    def __init__(self, preset_id: DeploymentPresetID) -> None:
        self._preset_id = preset_id

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[PresetResourceSlotRow]]:
        return sa.select(PresetResourceSlotRow).where(
            PresetResourceSlotRow.preset_id == self._preset_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: PresetResourceSlotRow) -> ResourceSlotEntryData:
        return ResourceSlotEntryData(
            resource_type=row.slot_name,
            quantity=str(row.quantity),
        )
