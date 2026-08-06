"""Devices discovered on agents and their attachment to kernels."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.agent import AgentUUID
from ai.backend.common.types import DeviceId, DeviceName, KernelId
from ai.backend.manager.models.base import (
    GUID,
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
    """A physical device on an agent; device_id is agent-local, hence the composite PK."""

    __tablename__ = "devices"

    agent_uuid: Mapped[AgentUUID] = mapped_column("agent_uuid", GUID(AgentUUID), primary_key=True)
    device_name: Mapped[DeviceName] = mapped_column(
        "device_name", sa.String(length=64), primary_key=True
    )
    device_id: Mapped[DeviceId] = mapped_column(
        "device_id", sa.String(length=128), primary_key=True
    )
    model_name: Mapped[str] = mapped_column("model_name", sa.String(length=255), nullable=False)

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["agent_uuid"],
            ["agents.uuid"],
            name="fk_devices_agent_uuid_agents",
            ondelete="CASCADE",
        ),
    )


class KernelDeviceRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """Kernel-device junction; ``data`` is the capacity allocated to the kernel,
    not the device's physical capacity."""

    __tablename__ = "kernel_devices"

    kernel_id: Mapped[KernelId] = mapped_column("kernel_id", KernelIDColumnType, primary_key=True)
    agent_uuid: Mapped[AgentUUID] = mapped_column("agent_uuid", GUID(AgentUUID), primary_key=True)
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
            ["agent_uuid", "device_name", "device_id"],
            ["devices.agent_uuid", "devices.device_name", "devices.device_id"],
            name="fk_kernel_devices_device_devices",
            ondelete="CASCADE",
        ),
        # for the devices-side FK cascade
        sa.Index("ix_kernel_devices_device", "agent_uuid", "device_name", "device_id"),
    )
