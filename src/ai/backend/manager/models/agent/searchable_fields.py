"""What an agent search can filter and order by, and how an agent row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentData, AgentStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.entity_label.searchable_fields import (
    EntityLabelCorrelation,
    EntityLabelSearchableFields,
)
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToManyCorrelation
from ai.backend.manager.models.specs.search.field import NestedSearchableField, SearchableField
from ai.backend.manager.models.specs.search.usage import UsedByConditions


class _AgentOwnFields(RowDataConverter[AgentRow, AgentData]):
    """The agent's own columns.

    ``compute_plugins`` is JSONB and ``public_key`` is a key, so both slots stay empty
    for either.
    """

    uuid = SearchableField(AgentRow.uuid, UUIDConditions(AgentRow.uuid), ColumnOrder(AgentRow.uuid))
    id = SearchableField(AgentRow.id, StringConditions(AgentRow.id), ColumnOrder(AgentRow.id))
    status = SearchableField(
        AgentRow.status,
        EnumConditions(AgentRow.status, AgentStatus),
        ColumnOrder(AgentRow.status),
    )
    status_changed = SearchableField(
        AgentRow.status_changed,
        DateTimeConditions(AgentRow.status_changed),
        ColumnOrder(AgentRow.status_changed),
    )
    region = SearchableField(
        AgentRow.region, StringConditions(AgentRow.region), ColumnOrder(AgentRow.region)
    )
    resource_group = SearchableField(
        AgentRow.scaling_group,
        StringConditions(AgentRow.scaling_group),
        ColumnOrder(AgentRow.scaling_group),
    )
    resource_group_id = SearchableField(
        AgentRow.resource_group_id,
        UUIDConditions(AgentRow.resource_group_id),
        ColumnOrder(AgentRow.resource_group_id),
    )
    schedulable = SearchableField(
        AgentRow.schedulable,
        BoolConditions(AgentRow.schedulable),
        ColumnOrder(AgentRow.schedulable),
    )
    addr = SearchableField(
        AgentRow.addr, StringConditions(AgentRow.addr), ColumnOrder(AgentRow.addr)
    )
    public_host = SearchableField(
        AgentRow.public_host,
        StringConditions(AgentRow.public_host),
        ColumnOrder(AgentRow.public_host),
    )
    public_key = SearchableField(AgentRow.public_key, None, None)
    first_contact = SearchableField(
        AgentRow.first_contact,
        DateTimeConditions(AgentRow.first_contact),
        ColumnOrder(AgentRow.first_contact),
    )
    lost_at = SearchableField(
        AgentRow.lost_at, DateTimeConditions(AgentRow.lost_at), ColumnOrder(AgentRow.lost_at)
    )
    version = SearchableField(
        AgentRow.version, StringConditions(AgentRow.version), ColumnOrder(AgentRow.version)
    )
    architecture = SearchableField(
        AgentRow.architecture,
        StringConditions(AgentRow.architecture),
        ColumnOrder(AgentRow.architecture),
    )
    compute_plugins = SearchableField(AgentRow.compute_plugins, None, None)
    auto_terminate_abusing_kernel = SearchableField(
        AgentRow.auto_terminate_abusing_kernel,
        BoolConditions(AgentRow.auto_terminate_abusing_kernel),
        ColumnOrder(AgentRow.auto_terminate_abusing_kernel),
    )

    @override
    def to_data(self, row: AgentRow) -> AgentData:
        return AgentData(
            uuid=self.uuid.read(row),
            id=AgentId(self.id.read(row)),
            status=self.status.read(row),
            status_changed=self.status_changed.read(row),
            region=self.region.read(row),
            resource_group=self.resource_group.read(row),
            schedulable=self.schedulable.read(row),
            addr=self.addr.read(row),
            public_host=self.public_host.read(row),
            first_contact=self.first_contact.read(row),
            lost_at=self.lost_at.read(row),
            version=self.version.read(row),
            architecture=self.architecture.read(row),
            compute_plugins=self.compute_plugins.read(row),
            public_key=self.public_key.read(row),
            auto_terminate_abusing_kernel=self.auto_terminate_abusing_kernel.read(row),
        )


class _AgentNestedFields:
    """Rows of other tables the agent owns: its labels."""

    labels = NestedSearchableField(
        EntityLabelSearchableFields.own,
        EntityLabelCorrelation(AgentRow, AgentEntityType(), AgentRow.uuid),
    )


class _AgentUsage:
    """Uses between an agent and other entities."""

    sessions = UsedByConditions[SessionID](
        ToManyCorrelation(KernelRow, AgentRow, KernelRow.agent == AgentRow.id),
        KernelRow.session_id,
    )
    """Agents a session runs a kernel on."""


class _AgentLinkedEntities:
    """How an agent connects to other entities; the other entity's permission governs."""

    usage = _AgentUsage


class AgentSearchableFields:
    own = _AgentOwnFields()
    nested = _AgentNestedFields
    linked = _AgentLinkedEntities
