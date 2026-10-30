"""What a resource preset search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ResourcePresetOwnFields(RowDataConverter[ResourcePresetRow, ResourcePresetData]):
    """The resource preset's own columns."""

    id = SearchableField(
        ResourcePresetRow.id,
        UUIDConditions(ResourcePresetRow.id),
        ColumnOrder(ResourcePresetRow.id),
    )
    name = SearchableField(
        ResourcePresetRow.name,
        StringConditions(ResourcePresetRow.name),
        ColumnOrder(ResourcePresetRow.name),
    )
    resource_slots = SearchableField(ResourcePresetRow.resource_slots, None, None)
    """Impossible: a JSON document of slot amounts."""
    shared_memory = SearchableField(
        ResourcePresetRow.shared_memory,
        IntConditions(ResourcePresetRow.shared_memory),
        ColumnOrder(ResourcePresetRow.shared_memory),
    )
    resource_group_name = SearchableField(
        ResourcePresetRow.scaling_group_name,
        StringConditions(ResourcePresetRow.scaling_group_name),
        ColumnOrder(ResourcePresetRow.scaling_group_name),
    )
    """The resource group the preset is bound to; unset is offered to everyone."""

    @override
    def to_data(self, row: ResourcePresetRow) -> ResourcePresetData:
        return ResourcePresetData(
            id=self.id.read(row),
            name=self.name.read(row),
            resource_slots=self.resource_slots.read(row),
            shared_memory=self.shared_memory.read(row),
            resource_group_name=self.resource_group_name.read(row),
        )


class ResourcePresetSearchableFields:
    own = _ResourcePresetOwnFields()
