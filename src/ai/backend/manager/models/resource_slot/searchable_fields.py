"""What a resource slot type search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.resource_slot.types import NumberFormatData, ResourceSlotTypeData
from ai.backend.manager.models.resource_slot.row import ResourceSlotTypeRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ResourceSlotTypeOwnFields(RowDataConverter[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """The slot type's own columns. ``number_format`` is JSON, so both slots stay empty."""

    uuid = SearchableField(
        ResourceSlotTypeRow.uuid,
        UUIDConditions(ResourceSlotTypeRow.uuid),
        ColumnOrder(ResourceSlotTypeRow.uuid),
    )
    slot_name = SearchableField(
        ResourceSlotTypeRow.slot_name,
        StringConditions(ResourceSlotTypeRow.slot_name),
        ColumnOrder(ResourceSlotTypeRow.slot_name),
    )
    slot_type = SearchableField(
        ResourceSlotTypeRow.slot_type,
        StringConditions(ResourceSlotTypeRow.slot_type),
        ColumnOrder(ResourceSlotTypeRow.slot_type),
    )
    required = SearchableField(
        ResourceSlotTypeRow.required,
        BoolConditions(ResourceSlotTypeRow.required),
        ColumnOrder(ResourceSlotTypeRow.required),
    )
    enabled = SearchableField(
        ResourceSlotTypeRow.enabled,
        BoolConditions(ResourceSlotTypeRow.enabled),
        ColumnOrder(ResourceSlotTypeRow.enabled),
    )
    display_name = SearchableField(
        ResourceSlotTypeRow.display_name,
        StringConditions(ResourceSlotTypeRow.display_name),
        ColumnOrder(ResourceSlotTypeRow.display_name),
    )
    description = SearchableField(
        ResourceSlotTypeRow.description,
        StringConditions(ResourceSlotTypeRow.description),
        ColumnOrder(ResourceSlotTypeRow.description),
    )
    display_unit = SearchableField(
        ResourceSlotTypeRow.display_unit,
        StringConditions(ResourceSlotTypeRow.display_unit),
        ColumnOrder(ResourceSlotTypeRow.display_unit),
    )
    display_icon = SearchableField(
        ResourceSlotTypeRow.display_icon,
        StringConditions(ResourceSlotTypeRow.display_icon),
        ColumnOrder(ResourceSlotTypeRow.display_icon),
    )
    number_format = SearchableField(ResourceSlotTypeRow.number_format, None, None)
    rank = SearchableField(
        ResourceSlotTypeRow.rank,
        IntConditions(ResourceSlotTypeRow.rank),
        ColumnOrder(ResourceSlotTypeRow.rank),
    )

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        number_format = self.number_format.read(row)
        return ResourceSlotTypeData(
            uuid=self.uuid.read(row),
            slot_name=self.slot_name.read(row),
            slot_type=self.slot_type.read(row),
            required=self.required.read(row),
            enabled=self.enabled.read(row),
            display_name=self.display_name.read(row),
            description=self.description.read(row),
            display_unit=self.display_unit.read(row),
            display_icon=self.display_icon.read(row),
            number_format=NumberFormatData(
                binary=number_format.binary, round_length=number_format.round_length
            ),
            rank=self.rank.read(row),
        )


class ResourceSlotTypeSearchableFields:
    own = _ResourceSlotTypeOwnFields()
