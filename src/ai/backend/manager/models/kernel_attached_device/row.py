"""Devices attached to each kernel, replacing the kernels.attached_devices JSONB."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.types import DeviceId, DeviceName, KernelId
from ai.backend.manager.models.base import (
    Base,
    DeviceCapacityEntry,
    KernelIDColumnType,
    PydanticListColumn,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("KernelAttachedDeviceRow",)


class KernelAttachedDeviceRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """One row per device attached to a kernel.

    Composite primary key: (kernel_id, device_name, device_id) — rows are
    write-once (INSERT ON CONFLICT DO NOTHING) and removed only by FK cascade.
    """

    __tablename__ = "kernel_attached_devices"

    kernel_id: Mapped[KernelId] = mapped_column("kernel_id", KernelIDColumnType, primary_key=True)
    device_name: Mapped[DeviceName] = mapped_column(
        "device_name", sa.String(length=64), primary_key=True
    )
    device_id: Mapped[DeviceId] = mapped_column(
        "device_id", sa.String(length=128), primary_key=True
    )
    model_name: Mapped[str] = mapped_column("model_name", sa.String(length=255), nullable=False)
    # Plugin capacity map normalized to typed (name, value) entries.
    data: Mapped[list[DeviceCapacityEntry]] = mapped_column(
        "data",
        PydanticListColumn(DeviceCapacityEntry),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name="fk_kernel_attached_devices_kernel_id_kernels",
            ondelete="CASCADE",
        ),
    )
