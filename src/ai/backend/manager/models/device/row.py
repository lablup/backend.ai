"""Devices discovered on agents and their attachment to kernels, replacing the
kernels.attached_devices JSONB."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.types import AgentId, DeviceId, DeviceName, KernelId
from ai.backend.manager.models.base import (
    Base,
    DeviceCapacityEntry,
    KernelIDColumnType,
    PydanticListColumn,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = (
    "DeviceRow",
    "KernelDeviceRow",
)


class DeviceRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """A physical device discovered on an agent.

    Natural composite primary key: (agent_id, device_name, device_id) —
    device_id is agent-local (cpu "0", mem "root"), so it is unique only
    within an agent and a device kind.
    """

    __tablename__ = "devices"

    agent_id: Mapped[AgentId] = mapped_column("agent_id", sa.String(length=64), primary_key=True)
    device_name: Mapped[DeviceName] = mapped_column(
        "device_name", sa.String(length=64), primary_key=True
    )
    device_id: Mapped[DeviceId] = mapped_column(
        "device_id", sa.String(length=128), primary_key=True
    )
    model_name: Mapped[str] = mapped_column("model_name", sa.String(length=255), nullable=False)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_devices_agent_id_agents",
            ondelete="CASCADE",
        ),
    )


class KernelDeviceRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """Junction between kernels and devices.

    Rows are write-once (INSERT ON CONFLICT DO NOTHING) and removed only by
    FK cascade. ``data`` holds the capacity allocated to this kernel, not the
    device's physical capacity — the same device carries different values per
    kernel (e.g. fractional GPU shares).
    """

    __tablename__ = "kernel_devices"

    kernel_id: Mapped[KernelId] = mapped_column("kernel_id", KernelIDColumnType, primary_key=True)
    agent_id: Mapped[AgentId] = mapped_column("agent_id", sa.String(length=64), primary_key=True)
    device_name: Mapped[DeviceName] = mapped_column(
        "device_name", sa.String(length=64), primary_key=True
    )
    device_id: Mapped[DeviceId] = mapped_column(
        "device_id", sa.String(length=128), primary_key=True
    )
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
            name="fk_kernel_devices_kernel_id_kernels",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id", "device_name", "device_id"],
            ["devices.agent_id", "devices.device_name", "devices.device_id"],
            name="fk_kernel_devices_device_devices",
            ondelete="CASCADE",
        ),
        # Supports the devices-side FK cascade (agent removal) without a full
        # scan; kernel-side consumers are covered by the PK prefix.
        sa.Index("ix_kernel_devices_device", "agent_id", "device_name", "device_id"),
    )
