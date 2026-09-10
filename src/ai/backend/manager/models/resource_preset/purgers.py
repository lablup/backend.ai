"""Purge specs for the resource_presets table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ResourcePresetPurger(EntityPurger[ResourcePresetRow, ResourcePresetData]):
    """Removes a resource preset along with the scope it was."""

    preset_id: ResourcePresetID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourcePresetRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return row.to_dataclass()
