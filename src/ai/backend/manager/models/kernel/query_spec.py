"""What a kernel search can filter and order by."""

from __future__ import annotations

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.field import QueryColumn


class _KernelOwnColumns:
    """The kernel's own columns a session read reaches."""

    id = QueryColumn(KernelRow.id, UUIDConditions(KernelRow.id), ColumnOrder(KernelRow.id))
    session_id = QueryColumn(
        KernelRow.session_id,
        UUIDConditions(KernelRow.session_id),
        ColumnOrder(KernelRow.session_id),
    )
    status = QueryColumn(
        KernelRow.status,
        EnumConditions(KernelRow.status, KernelStatus),
        ColumnOrder(KernelRow.status),
    )
    agent = QueryColumn(
        KernelRow.agent, StringConditions(KernelRow.agent), ColumnOrder(KernelRow.agent)
    )
    cluster_mode = QueryColumn(
        KernelRow.cluster_mode,
        StringConditions(KernelRow.cluster_mode),
        ColumnOrder(KernelRow.cluster_mode),
    )
    cluster_role = QueryColumn(
        KernelRow.cluster_role,
        StringConditions(KernelRow.cluster_role),
        ColumnOrder(KernelRow.cluster_role),
    )
    cluster_idx = QueryColumn(
        KernelRow.cluster_idx,
        IntConditions(KernelRow.cluster_idx),
        ColumnOrder(KernelRow.cluster_idx),
    )
    cluster_hostname = QueryColumn(
        KernelRow.cluster_hostname,
        StringConditions(KernelRow.cluster_hostname),
        ColumnOrder(KernelRow.cluster_hostname),
    )
    resource_group_name = QueryColumn(
        KernelRow.scaling_group,
        StringConditions(KernelRow.scaling_group),
        ColumnOrder(KernelRow.scaling_group),
    )
    resource_group_id = QueryColumn(
        KernelRow.resource_group_id,
        UUIDConditions(KernelRow.resource_group_id),
        ColumnOrder(KernelRow.resource_group_id),
    )
    starts_at = QueryColumn(
        KernelRow.starts_at,
        DateTimeConditions(KernelRow.starts_at),
        ColumnOrder(KernelRow.starts_at),
    )
    terminated_at = QueryColumn(
        KernelRow.terminated_at,
        DateTimeConditions(KernelRow.terminated_at),
        ColumnOrder(KernelRow.terminated_at),
    )
    last_observed_at = QueryColumn(
        KernelRow.last_observed_at,
        DateTimeConditions(KernelRow.last_observed_at),
        ColumnOrder(KernelRow.last_observed_at),
    )
    created_at = QueryColumn(
        KernelRow.created_at,
        DateTimeConditions(KernelRow.created_at),
        ColumnOrder(KernelRow.created_at),
    )


class KernelQuerySpec:
    own = _KernelOwnColumns
