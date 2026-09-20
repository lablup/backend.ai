"""What a kernel search can filter and order by."""

from __future__ import annotations

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.field import SearchableField


class _KernelOwnFields:
    """The kernel's own columns a session read reaches."""

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


class KernelSearchableFields:
    own = _KernelOwnFields
