"""Lookup specs for the resource presets table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ResourcePresetNameLookup(DataLookup[ResourcePresetRow, ResourcePresetID]):
    """Reads the preset a name refers to, within a resource group, or across all of them
    when none is given."""

    name: str
    resource_group_name: str | None = None

    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        conditions: list[QueryCondition] = [lambda: ResourcePresetRow.name == self.name]
        if self.resource_group_name is not None:
            conditions.append(
                lambda: ResourcePresetRow.scaling_group_name == self.resource_group_name
            )
        return conditions

    @override
    def to_entity_id(self, row: ResourcePresetRow) -> ResourcePresetID:
        return row.id
