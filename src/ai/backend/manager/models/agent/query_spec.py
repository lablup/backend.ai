"""What an agent search can filter and order by, and how an agent row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.agent import AgentEntityType
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import AgentId
from ai.backend.manager.data.agent.types import AgentData, AgentStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.entity_label.query_spec import (
    EntityLabelCorrelation,
    EntityLabelQuerySpec,
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
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn
from ai.backend.manager.models.specs.search.usage import UsedByConditions


class _AgentOwnColumns(RowDataConverter[AgentRow, AgentData]):
    """The agent's own columns.

    ``compute_plugins`` is JSONB and ``public_key`` is a key, so both slots stay empty
    for either.
    """

    uuid = QueryColumn(AgentRow.uuid, UUIDConditions(AgentRow.uuid), ColumnOrder(AgentRow.uuid))
    id = QueryColumn(AgentRow.id, StringConditions(AgentRow.id), ColumnOrder(AgentRow.id))
    status = QueryColumn(
        AgentRow.status,
        EnumConditions(AgentRow.status, AgentStatus),
        ColumnOrder(AgentRow.status),
    )
    status_changed = QueryColumn(
        AgentRow.status_changed,
        DateTimeConditions(AgentRow.status_changed),
        ColumnOrder(AgentRow.status_changed),
    )
    region = QueryColumn(
        AgentRow.region, StringConditions(AgentRow.region), ColumnOrder(AgentRow.region)
    )
    resource_group = QueryColumn(
        AgentRow.scaling_group,
        StringConditions(AgentRow.scaling_group),
        ColumnOrder(AgentRow.scaling_group),
    )
    resource_group_id = QueryColumn(
        AgentRow.resource_group_id,
        UUIDConditions(AgentRow.resource_group_id),
        ColumnOrder(AgentRow.resource_group_id),
    )
    schedulable = QueryColumn(
        AgentRow.schedulable,
        BoolConditions(AgentRow.schedulable),
        ColumnOrder(AgentRow.schedulable),
    )
    addr = QueryColumn(AgentRow.addr, StringConditions(AgentRow.addr), ColumnOrder(AgentRow.addr))
    public_host = QueryColumn(
        AgentRow.public_host,
        StringConditions(AgentRow.public_host),
        ColumnOrder(AgentRow.public_host),
    )
    public_key = QueryColumn(AgentRow.public_key, None, None)
    first_contact = QueryColumn(
        AgentRow.first_contact,
        DateTimeConditions(AgentRow.first_contact),
        ColumnOrder(AgentRow.first_contact),
    )
    lost_at = QueryColumn(
        AgentRow.lost_at, DateTimeConditions(AgentRow.lost_at), ColumnOrder(AgentRow.lost_at)
    )
    version = QueryColumn(
        AgentRow.version, StringConditions(AgentRow.version), ColumnOrder(AgentRow.version)
    )
    architecture = QueryColumn(
        AgentRow.architecture,
        StringConditions(AgentRow.architecture),
        ColumnOrder(AgentRow.architecture),
    )
    compute_plugins = QueryColumn(AgentRow.compute_plugins, None, None)
    auto_terminate_abusing_kernel = QueryColumn(
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


class _AgentNestedColumns:
    """Rows of other tables the agent owns: its labels."""

    labels = NestedQueryColumn(
        EntityLabelQuerySpec.own,
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


class AgentQuerySpec:
    own = _AgentOwnColumns()
    nested = _AgentNestedColumns
    linked = _AgentLinkedEntities
