"""Resource Slot Normalization Row models.

Database models for normalized resource slot management:
- ResourceSlotTypeRow: Registry of known resource slot types and display metadata
- AgentResourceRow: Per-agent, per-slot resource capacity and usage
- ResourceAllocationRow: Per-kernel, per-slot resource allocation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import (
    GUID,
    Base,
)

__all__ = (
    "ResourceSlotTypeRow",
    "AgentResourceRow",
    "ResourceAllocationRow",
)


class ResourceSlotTypeRow(Base):  # type: ignore[misc]
    """Registry of known resource slot types with display metadata.

    Primary key is slot_name (e.g., 'cpu', 'mem', 'cuda.device').
    """

    __tablename__ = "resource_slot_types"

    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    slot_type: Mapped[str] = mapped_column("slot_type", sa.String(length=16), nullable=False)
    display_name: Mapped[str | None] = mapped_column(
        "display_name", sa.String(length=128), nullable=True
    )
    rank: Mapped[int] = mapped_column(
        "rank", sa.Integer, nullable=False, server_default=sa.text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


class AgentResourceRow(Base):  # type: ignore[misc]
    """Per-agent, per-slot resource capacity and usage.

    Composite primary key: (agent_id, slot_name).
    """

    __tablename__ = "agent_resources"

    agent_id: Mapped[str] = mapped_column("agent_id", sa.String(length=64), primary_key=True)
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    capacity: Mapped[Decimal] = mapped_column(
        "capacity", sa.Numeric(precision=24, scale=6), nullable=False
    )
    used: Mapped[Decimal] = mapped_column(
        "used", sa.Numeric(precision=24, scale=6), nullable=False, server_default=sa.text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            name="fk_agent_resources_agent_id_agents",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_agent_resources_slot_name_resource_slot_types",
        ),
        sa.Index("ix_agent_resources_slot_name", "slot_name"),
        sa.Index(
            "ix_agent_resources_agent_avail",
            "agent_id",
            "slot_name",
            "capacity",
            "used",
        ),
    )


class ResourceAllocationRow(Base):  # type: ignore[misc]
    """Per-kernel, per-slot resource allocation.

    Composite primary key: (kernel_id, slot_name).
    """

    __tablename__ = "resource_allocations"

    kernel_id: Mapped[uuid.UUID] = mapped_column("kernel_id", GUID, primary_key=True)
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), primary_key=True)
    requested: Mapped[Decimal] = mapped_column(
        "requested", sa.Numeric(precision=24, scale=6), nullable=False
    )
    used: Mapped[Decimal | None] = mapped_column(
        "used", sa.Numeric(precision=24, scale=6), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    used_at: Mapped[datetime | None] = mapped_column(
        "used_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )
    free_at: Mapped[datetime | None] = mapped_column(
        "free_at",
        sa.DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        sa.ForeignKeyConstraint(
            ["kernel_id"],
            ["kernels.id"],
            name="fk_resource_allocations_kernel_id_kernels",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["slot_name"],
            ["resource_slot_types.slot_name"],
            name="fk_resource_allocations_slot_name_resource_slot_types",
        ),
        sa.Index("ix_resource_allocations_slot_name", "slot_name"),
        sa.Index("ix_ra_kernel_slot", "kernel_id", "slot_name"),
        sa.Index(
            "ix_ra_occupied",
            "kernel_id",
            "slot_name",
            postgresql_where=sa.text("free_at IS NULL"),
        ),
    )
