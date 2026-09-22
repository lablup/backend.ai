"""What a resource slot search can filter and order by, and how a row becomes data.

Each slot row lives under the entity that owns it -- an agent, a kernel, a deployment
revision, a deployment preset -- and the slot catalog is the entity of its own.
"""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.manager.data.deployment.types import RevisionResourceSlotData
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    NumberFormatData,
    ResourceAllocationData,
    ResourceSlotTypeData,
)
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    PresetResourceSlotRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.number import DecimalConditions
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


class _AgentResourceOwnFields(RowDataConverter[AgentResourceRow, AgentResourceData]):
    """The agent slot row's own columns."""

    id = SearchableField(
        AgentResourceRow.id,
        UUIDConditions(AgentResourceRow.id),
        ColumnOrder(AgentResourceRow.id),
    )
    agent_id = SearchableField(
        AgentResourceRow.agent_id,
        StringConditions(AgentResourceRow.agent_id),
        ColumnOrder(AgentResourceRow.agent_id),
    )
    agent_uuid = SearchableField(
        AgentResourceRow.agent_uuid,
        UUIDConditions(AgentResourceRow.agent_uuid),
        ColumnOrder(AgentResourceRow.agent_uuid),
    )
    slot_name = SearchableField(
        AgentResourceRow.slot_name,
        StringConditions(AgentResourceRow.slot_name),
        ColumnOrder(AgentResourceRow.slot_name),
    )
    capacity = SearchableField(
        AgentResourceRow.capacity,
        DecimalConditions(AgentResourceRow.capacity),
        ColumnOrder(AgentResourceRow.capacity),
    )
    reserved = SearchableField(
        AgentResourceRow.reserved,
        DecimalConditions(AgentResourceRow.reserved),
        ColumnOrder(AgentResourceRow.reserved),
    )
    prereserved = SearchableField(
        AgentResourceRow.prereserved,
        DecimalConditions(AgentResourceRow.prereserved),
        ColumnOrder(AgentResourceRow.prereserved),
    )
    used = SearchableField(
        AgentResourceRow.used,
        DecimalConditions(AgentResourceRow.used),
        ColumnOrder(AgentResourceRow.used),
    )

    @override
    def to_data(self, row: AgentResourceRow) -> AgentResourceData:
        return AgentResourceData(
            id=self.id.read(row),
            agent_id=self.agent_id.read(row),
            slot_name=self.slot_name.read(row),
            capacity=self.capacity.read(row),
            reserved=self.reserved.read(row),
            used=self.used.read(row),
        )


class _ResourceAllocationOwnFields(RowDataConverter[ResourceAllocationRow, ResourceAllocationData]):
    """The allocation row's own columns."""

    id = SearchableField(
        ResourceAllocationRow.id,
        UUIDConditions(ResourceAllocationRow.id),
        ColumnOrder(ResourceAllocationRow.id),
    )
    kernel_id = SearchableField(
        ResourceAllocationRow.kernel_id,
        UUIDConditions(ResourceAllocationRow.kernel_id),
        ColumnOrder(ResourceAllocationRow.kernel_id),
    )
    slot_name = SearchableField(
        ResourceAllocationRow.slot_name,
        StringConditions(ResourceAllocationRow.slot_name),
        ColumnOrder(ResourceAllocationRow.slot_name),
    )
    requested = SearchableField(
        ResourceAllocationRow.requested,
        DecimalConditions(ResourceAllocationRow.requested),
        ColumnOrder(ResourceAllocationRow.requested),
    )
    prereserved = SearchableField(
        ResourceAllocationRow.prereserved,
        DecimalConditions(ResourceAllocationRow.prereserved),
        ColumnOrder(ResourceAllocationRow.prereserved),
    )
    reserved = SearchableField(
        ResourceAllocationRow.reserved,
        DecimalConditions(ResourceAllocationRow.reserved),
        ColumnOrder(ResourceAllocationRow.reserved),
    )
    used = SearchableField(
        ResourceAllocationRow.used,
        DecimalConditions(ResourceAllocationRow.used),
        ColumnOrder(ResourceAllocationRow.used),
    )
    prereserved_at = SearchableField(
        ResourceAllocationRow.prereserved_at,
        DateTimeConditions(ResourceAllocationRow.prereserved_at),
        ColumnOrder(ResourceAllocationRow.prereserved_at),
    )
    reserved_at = SearchableField(
        ResourceAllocationRow.reserved_at,
        DateTimeConditions(ResourceAllocationRow.reserved_at),
        ColumnOrder(ResourceAllocationRow.reserved_at),
    )
    used_at = SearchableField(
        ResourceAllocationRow.used_at,
        DateTimeConditions(ResourceAllocationRow.used_at),
        ColumnOrder(ResourceAllocationRow.used_at),
    )
    free_at = SearchableField(
        ResourceAllocationRow.free_at,
        DateTimeConditions(ResourceAllocationRow.free_at),
        ColumnOrder(ResourceAllocationRow.free_at),
    )

    @override
    def to_data(self, row: ResourceAllocationRow) -> ResourceAllocationData:
        return ResourceAllocationData(
            id=self.id.read(row),
            kernel_id=self.kernel_id.read(row),
            slot_name=self.slot_name.read(row),
            requested=self.requested.read(row),
            used=self.used.read(row),
        )


class _RevisionResourceSlotOwnFields(
    RowDataConverter[DeploymentRevisionResourceSlotRow, RevisionResourceSlotData]
):
    """The revision slot row's own columns."""

    id = SearchableField(
        DeploymentRevisionResourceSlotRow.id,
        UUIDConditions(DeploymentRevisionResourceSlotRow.id),
        ColumnOrder(DeploymentRevisionResourceSlotRow.id),
    )
    revision_id = SearchableField(
        DeploymentRevisionResourceSlotRow.revision_id,
        UUIDConditions(DeploymentRevisionResourceSlotRow.revision_id),
        ColumnOrder(DeploymentRevisionResourceSlotRow.revision_id),
    )
    slot_name = SearchableField(
        DeploymentRevisionResourceSlotRow.slot_name,
        StringConditions(DeploymentRevisionResourceSlotRow.slot_name),
        ColumnOrder(DeploymentRevisionResourceSlotRow.slot_name),
    )
    quantity = SearchableField(
        DeploymentRevisionResourceSlotRow.quantity,
        DecimalConditions(DeploymentRevisionResourceSlotRow.quantity),
        ColumnOrder(DeploymentRevisionResourceSlotRow.quantity),
    )

    @override
    def to_data(self, row: DeploymentRevisionResourceSlotRow) -> RevisionResourceSlotData:
        return RevisionResourceSlotData(
            revision_id=self.revision_id.read(row),
            slot_name=self.slot_name.read(row),
            quantity=self.quantity.read(row),
        )


class _PresetResourceSlotOwnFields(RowDataConverter[PresetResourceSlotRow, PresetResourceSlotData]):
    """The preset slot row's own columns."""

    id = SearchableField(
        PresetResourceSlotRow.id,
        UUIDConditions(PresetResourceSlotRow.id),
        ColumnOrder(PresetResourceSlotRow.id),
    )
    preset_id = SearchableField(
        PresetResourceSlotRow.preset_id,
        UUIDConditions(PresetResourceSlotRow.preset_id),
        ColumnOrder(PresetResourceSlotRow.preset_id),
    )
    slot_name = SearchableField(
        PresetResourceSlotRow.slot_name,
        StringConditions(PresetResourceSlotRow.slot_name),
        ColumnOrder(PresetResourceSlotRow.slot_name),
    )
    quantity = SearchableField(
        PresetResourceSlotRow.quantity,
        DecimalConditions(PresetResourceSlotRow.quantity),
        ColumnOrder(PresetResourceSlotRow.quantity),
    )

    @override
    def to_data(self, row: PresetResourceSlotRow) -> PresetResourceSlotData:
        return PresetResourceSlotData(
            preset_id=DeploymentPresetID(self.preset_id.read(row)),
            slot_name=self.slot_name.read(row),
            quantity=self.quantity.read(row),
        )


class AgentResourceSearchableFields:
    own = _AgentResourceOwnFields()


class ResourceAllocationSearchableFields:
    own = _ResourceAllocationOwnFields()


class RevisionResourceSlotSearchableFields:
    own = _RevisionResourceSlotOwnFields()


class PresetResourceSlotSearchableFields:
    own = _PresetResourceSlotOwnFields()
