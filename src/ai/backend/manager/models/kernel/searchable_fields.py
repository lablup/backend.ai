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
from ai.backend.manager.models.specs.search.field import SearchableField


class _KernelOwnFields:
    """The kernel's own columns a session read reaches."""

    id = SearchableField(KernelRow.id, UUIDConditions(KernelRow.id), ColumnOrder(KernelRow.id))
    session_id = SearchableField(
        KernelRow.session_id,
        UUIDConditions(KernelRow.session_id),
        ColumnOrder(KernelRow.session_id),
    )
    status = SearchableField(
        KernelRow.status,
        EnumConditions(KernelRow.status, KernelStatus),
        ColumnOrder(KernelRow.status),
    )
    agent = SearchableField(
        KernelRow.agent, StringConditions(KernelRow.agent), ColumnOrder(KernelRow.agent)
    )
    cluster_mode = SearchableField(
        KernelRow.cluster_mode,
        StringConditions(KernelRow.cluster_mode),
        ColumnOrder(KernelRow.cluster_mode),
    )
    cluster_idx = SearchableField(
        KernelRow.cluster_idx,
        IntConditions(KernelRow.cluster_idx),
        ColumnOrder(KernelRow.cluster_idx),
    )
    cluster_hostname = SearchableField(
        KernelRow.cluster_hostname,
        StringConditions(KernelRow.cluster_hostname),
        ColumnOrder(KernelRow.cluster_hostname),
    )
    resource_group_name = SearchableField(
        KernelRow.scaling_group,
        StringConditions(KernelRow.scaling_group),
        ColumnOrder(KernelRow.scaling_group),
    )
    resource_group_id = SearchableField(
        KernelRow.resource_group_id,
        UUIDConditions(KernelRow.resource_group_id),
        ColumnOrder(KernelRow.resource_group_id),
    )
    starts_at = SearchableField(
        KernelRow.starts_at,
        DateTimeConditions(KernelRow.starts_at),
        ColumnOrder(KernelRow.starts_at),
    )
    terminated_at = SearchableField(
        KernelRow.terminated_at,
        DateTimeConditions(KernelRow.terminated_at),
        ColumnOrder(KernelRow.terminated_at),
    )
    last_observed_at = SearchableField(
        KernelRow.last_observed_at,
        DateTimeConditions(KernelRow.last_observed_at),
        ColumnOrder(KernelRow.last_observed_at),
    )
    created_at = SearchableField(
        KernelRow.created_at,
        DateTimeConditions(KernelRow.created_at),
        ColumnOrder(KernelRow.created_at),
    )


class KernelSearchableFields:
    own = _KernelOwnFields
