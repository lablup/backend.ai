"""Devices discovered on agents and their per-kernel capacity allocations."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.agent import AgentUUID
from ai.backend.common.types import DeviceId, DeviceName, KernelId
from ai.backend.manager.models.base import (
    GUID,
    Base,
    KernelIDColumnType,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = (
    "DeviceRow",
    "DeviceAllocationRow",
)


class DeviceRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """A physical device on an agent.

    ``designator`` is the plugin-assigned handle for the device (e.g. cpu core
    index ``"0"``, ``"root"``, a GPU UUID) and is unique only within
    ``(agent, device_name)``.
    """

    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    agent_uuid: Mapped[AgentUUID] = mapped_column("agent_uuid", GUID(AgentUUID), nullable=False)
    device_name: Mapped[DeviceName] = mapped_column(
        "device_name", sa.String(length=64), nullable=False
    )
    designator: Mapped[DeviceId] = mapped_column(
        "designator", sa.String(length=128), nullable=False
    )
    model_name: Mapped[str] = mapped_column("model_name", sa.String(length=255), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint(
            "agent_uuid",
            "device_name",
            "designator",
            name="uq_devices_agent_device_name_designator",
        ),
        sa.ForeignKeyConstraint(
            ["agent_uuid"],
            ["agents.uuid"],
            name="fk_devices_agent_uuid_agents",
            ondelete="CASCADE",
        ),
    )


class DeviceAllocationRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """Per-kernel, per-capacity-entry device allocation.

    ``quantity`` is the amount allocated to the kernel, not the device's physical
    capacity. A NULL ``quantity`` records a bare attachment for devices that report
    no capacity entries (e.g. the intrinsic ``mem`` device), with ``capacity_name``
    set to the device name.
    """

    __tablename__ = "device_allocations"

    id: Mapped[UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    kernel_id: Mapped[KernelId] = mapped_column("kernel_id", KernelIDColumnType, nullable=False)
    device_id: Mapped[UUID] = mapped_column("device_id", GUID, nullable=False)
    capacity_name: Mapped[str] = mapped_column(
        "capacity_name", sa.String(length=64), nullable=False
    )
    quantity: Mapped[Decimal | None] = mapped_column(
        "quantity", sa.Numeric(precision=24, scale=6), nullable=True
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "kernel_id",
            "device_id",
            "capacity_name",
            name="uq_device_allocations_kernel_device_capacity",
        ),
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name="fk_device_allocations_kernel_id_kernels",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            name="fk_device_allocations_device_id_devices",
            ondelete="CASCADE",
        ),
        # for the devices-side FK cascade
        sa.Index("ix_device_allocations_device_id", "device_id"),
    )
