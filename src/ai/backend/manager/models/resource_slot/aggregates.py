"""Kernel and session slot values aggregated from ``resource_allocations``.

``resource_allocations`` is the authority for the requested amounts, the current
occupancy, and what was ever allocated. The deprecated ``kernels.occupied_slots`` /
``kernels.requested_slots`` / ``sessions.occupying_slots`` /
``sessions.requested_slots`` columns are never read here.

Which of the three a reader wants: ``used`` for what an owner holds right now,
``allocated`` for what it ever held (it survives termination, so statistics and
billing read this one), ``requested`` for what was asked at enqueue.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import ColumnElement

from ai.backend.common.types import KernelId, ResourceSlot, SessionId
from ai.backend.manager.data.resource_slot.types import ResourceAllocationAggregate
from ai.backend.manager.models.base import ResourceSlotColumn
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.resource_slot.row import ResourceAllocationRow

type _OwnerIdColumn = InstrumentedAttribute[Any] | ColumnElement[Any]

__all__ = (
    "kernel_allocated_slots_expr",
    "kernel_requested_slots_expr",
    "kernel_used_slots_expr",
    "session_allocated_slots_expr",
    "session_requested_slots_expr",
    "session_used_slots_expr",
    "batch_load_kernel_allocations",
    "batch_load_session_allocations",
)


def _requested_value() -> ColumnElement[Any]:
    return sa.func.sum(ResourceAllocationRow.requested)


def _used_value() -> ColumnElement[Any]:
    return sa.func.sum(
        sa.func.coalesce(ResourceAllocationRow.used, ResourceAllocationRow.requested)
    ).filter(ResourceAllocationRow.free_at.is_(None))


def _allocated_value() -> ColumnElement[Any]:
    return sa.func.sum(ResourceAllocationRow.used).filter(ResourceAllocationRow.used_at.isnot(None))


def _kernel_join() -> Any:
    return sa.join(
        ResourceAllocationRow, KernelRow, ResourceAllocationRow.kernel_id == KernelRow.id
    )


def _as_slots(value_by_slot: Any) -> ColumnElement[ResourceSlot]:
    """Fold a (slot_name, value) selectable into a ``ResourceSlot``-typed scalar subquery."""
    return sa.type_coerce(
        sa.select(
            sa.func.coalesce(
                sa.func.jsonb_object_agg(
                    value_by_slot.c.slot_name, sa.cast(value_by_slot.c.value, sa.Text)
                ).filter(value_by_slot.c.value.isnot(None)),
                sa.text("'{}'::jsonb"),
            )
        )
        .select_from(value_by_slot)
        .scalar_subquery(),
        ResourceSlotColumn(),
    )


def _kernel_slots_expr(
    value_column: ColumnElement[Any], kernel_id: _OwnerIdColumn
) -> ColumnElement[ResourceSlot]:
    return _as_slots(
        sa.select(
            ResourceAllocationRow.slot_name.label("slot_name"),
            value_column.label("value"),
        )
        .where(ResourceAllocationRow.kernel_id == kernel_id)
        .group_by(ResourceAllocationRow.slot_name)
        .correlate_except(ResourceAllocationRow)
        .subquery()
        .lateral()
    )


def _session_slots_expr(
    value_column: ColumnElement[Any], session_id: _OwnerIdColumn
) -> ColumnElement[ResourceSlot]:
    return _as_slots(
        sa.select(
            ResourceAllocationRow.slot_name.label("slot_name"),
            value_column.label("value"),
        )
        .select_from(_kernel_join())
        .where(KernelRow.session_id == session_id)
        .group_by(ResourceAllocationRow.slot_name)
        .correlate_except(ResourceAllocationRow, KernelRow)
        .subquery()
        .lateral()
    )


def kernel_requested_slots_expr(kernel_id: _OwnerIdColumn) -> ColumnElement[ResourceSlot]:
    """A ``ResourceSlot``-typed scalar subquery of one kernel's requested slots."""
    return _kernel_slots_expr(_requested_value(), kernel_id)


def kernel_used_slots_expr(kernel_id: _OwnerIdColumn) -> ColumnElement[ResourceSlot]:
    """A ``ResourceSlot``-typed scalar subquery of what one kernel holds right now."""
    return _kernel_slots_expr(_used_value(), kernel_id)


def kernel_allocated_slots_expr(kernel_id: _OwnerIdColumn) -> ColumnElement[ResourceSlot]:
    """A ``ResourceSlot``-typed scalar subquery of what one kernel ever held."""
    return _kernel_slots_expr(_allocated_value(), kernel_id)


def session_requested_slots_expr(session_id: _OwnerIdColumn) -> ColumnElement[ResourceSlot]:
    """A ``ResourceSlot``-typed scalar subquery of one session's requested slots."""
    return _session_slots_expr(_requested_value(), session_id)


def session_used_slots_expr(session_id: _OwnerIdColumn) -> ColumnElement[ResourceSlot]:
    """A ``ResourceSlot``-typed scalar subquery of what one session holds right now."""
    return _session_slots_expr(_used_value(), session_id)


def session_allocated_slots_expr(session_id: _OwnerIdColumn) -> ColumnElement[ResourceSlot]:
    """A ``ResourceSlot``-typed scalar subquery of what one session ever held."""
    return _session_slots_expr(_allocated_value(), session_id)


def _rows_to_aggregates(
    rows: Sequence[Any], key_attr: str
) -> dict[Any, ResourceAllocationAggregate]:
    slots: dict[Any, tuple[ResourceSlot, ResourceSlot, ResourceSlot]] = {}
    for row in rows:
        key = getattr(row, key_attr)
        if key not in slots:
            slots[key] = (ResourceSlot(), ResourceSlot(), ResourceSlot())
        requested, used, allocated = slots[key]
        if row.requested is not None:
            requested[row.slot_name] = row.requested
        if row.used is not None:
            used[row.slot_name] = row.used
        if row.allocated is not None:
            allocated[row.slot_name] = row.allocated
    return {
        key: ResourceAllocationAggregate(requested=requested, used=used, allocated=allocated)
        for key, (requested, used, allocated) in slots.items()
    }


async def batch_load_kernel_allocations(
    db_session: SASession,
    kernel_ids: Sequence[KernelId],
) -> dict[KernelId, ResourceAllocationAggregate]:
    """Aggregate ``resource_allocations`` per kernel."""
    if not kernel_ids:
        return {}
    stmt = (
        sa.select(
            ResourceAllocationRow.kernel_id.label("kernel_id"),
            ResourceAllocationRow.slot_name.label("slot_name"),
            _requested_value().label("requested"),
            _used_value().label("used"),
            _allocated_value().label("allocated"),
        )
        .where(ResourceAllocationRow.kernel_id.in_(kernel_ids))
        .group_by(ResourceAllocationRow.kernel_id, ResourceAllocationRow.slot_name)
    )
    rows = (await db_session.execute(stmt)).all()
    return {KernelId(key): agg for key, agg in _rows_to_aggregates(rows, "kernel_id").items()}


async def batch_load_session_allocations(
    db_session: SASession,
    session_ids: Sequence[SessionId],
) -> dict[SessionId, ResourceAllocationAggregate]:
    """Aggregate ``resource_allocations`` per session, summed over its kernels."""
    if not session_ids:
        return {}
    stmt = (
        sa.select(
            KernelRow.session_id.label("session_id"),
            ResourceAllocationRow.slot_name.label("slot_name"),
            _requested_value().label("requested"),
            _used_value().label("used"),
            _allocated_value().label("allocated"),
        )
        .select_from(_kernel_join())
        .where(KernelRow.session_id.in_(session_ids))
        .group_by(KernelRow.session_id, ResourceAllocationRow.slot_name)
    )
    rows = (await db_session.execute(stmt)).all()
    return {SessionId(key): agg for key, agg in _rows_to_aggregates(rows, "session_id").items()}
