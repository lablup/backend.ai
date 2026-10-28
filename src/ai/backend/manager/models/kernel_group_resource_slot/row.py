"""The kernel group's resource request, one row per slot.

Shared memory is not a slot; it is ``kernel_groups.shmem``.
"""

from __future__ import annotations

from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.manager.models.base import GUID, Base

__all__ = ("KernelGroupResourceSlotRow",)


class KernelGroupResourceSlotRow(Base):
    """Per-group, per-slot resource request, unique on (kernel_group_id, slot_name)."""

    __tablename__ = "kernel_group_resource_slots"
    __table_args__ = (sa.UniqueConstraint("kernel_group_id", "slot_name"),)

    id: Mapped[KernelGroupResourceSlotID] = mapped_column(
        "id",
        GUID(KernelGroupResourceSlotID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    kernel_group_id: Mapped[KernelGroupID] = mapped_column(
        "kernel_group_id",
        GUID(KernelGroupID),
        sa.ForeignKey("kernel_groups.id", ondelete="RESTRICT"),
        nullable=False,
    )
    slot_name: Mapped[ResourceSlotName] = mapped_column(
        "slot_name",
        sa.String(length=64),
        sa.ForeignKey("resource_slot_types.slot_name"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(
        "quantity", sa.Numeric(precision=24, scale=6), nullable=False
    )
