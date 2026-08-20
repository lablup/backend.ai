"""Lookup specs for the resource presets table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourcePresetNameLookup(DataLookup[ResourcePresetRow, ResourcePresetData]):
    """Reads the preset a name refers to, within a resource group or outside one."""

    name: str
    resource_group_name: str | None = None

    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [
            lambda: ResourcePresetRow.name == self.name,
            lambda: ResourcePresetRow.scaling_group_name.is_(None)
            if self.resource_group_name is None
            else ResourcePresetRow.scaling_group_name == self.resource_group_name,
        ]

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return row.to_dataclass()
