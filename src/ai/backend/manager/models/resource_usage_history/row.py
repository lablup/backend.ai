"""Resource Usage History Row models.

This module defines the database models for tracking resource usage history:

Tier 1 - Raw Data:
- KernelUsageRecordRow: Per-period kernel resource usage records

Tier 2 - Aggregation Cache:
- DomainUsageBucketRow: Domain-level period aggregation
- ProjectUsageBucketRow: Project-level period aggregation
- UserUsageBucketRow: User-level period aggregation (per project)

Tier 2b - Normalized Aggregation Entries (Phase 3):
- UsageBucketEntryRow: Per-slot normalized entries for usage buckets
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.base import (
    GUID,
    Base,
    ResourceSlotColumn,
)
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = (
    "KernelUsageRecordRow",
    "DomainUsageBucketRow",
    "ProjectUsageBucketRow",
    "UserUsageBucketRow",
    "UsageBucketEntryRow",
)


class KernelUsageRecordRow(Base):  # type: ignore[misc]
    """Per-period kernel resource usage records (raw data).

    Each record represents kernel resource usage during a specific
    period (period_start ~ period_end). Generated in 5-minute intervals
    by batch aggregation.

    Resource usage is stored in resource-seconds units (resource amount * duration).
    """

    __tablename__ = "kernel_usage_records"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    # Foreign keys (no FK constraints - referenced entities can be deleted)
    kernel_id: Mapped[uuid.UUID] = mapped_column("kernel_id", GUID, nullable=False, index=True)
    session_id: Mapped[uuid.UUID] = mapped_column("session_id", GUID, nullable=False)
    user_uuid: Mapped[uuid.UUID] = mapped_column("user_uuid", GUID, nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column("project_id", GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False, index=True
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        nullable=False,
    )

    # Period slice information
    period_start: Mapped[datetime] = mapped_column(
        "period_start", sa.DateTime(timezone=True), nullable=False
    )
    period_end: Mapped[datetime] = mapped_column(
        "period_end", sa.DateTime(timezone=True), nullable=False
    )

    # Resource usage for the period (resource-seconds unit)
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        "resource_usage", ResourceSlotColumn(), nullable=False, default=ResourceSlot
    )

    __table_args__ = (
        sa.Index("ix_kernel_usage_rg_period", "resource_group", "period_start"),
        sa.Index("ix_kernel_usage_rg_id_period", "resource_group_id", "period_start"),
        sa.Index("ix_kernel_usage_user_period", "user_uuid", "period_start"),
    )


class DomainUsageBucketRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    """Per-domain period-based resource usage aggregation.

    Cache summing all Project/User usage within the domain.
    Uses mutable bucket strategy with period_end extension.
    """

    __tablename__ = "domain_usage_buckets"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        nullable=False,
    )

    # Bucket period information
    period_start: Mapped[date] = mapped_column("period_start", sa.Date, nullable=False)
    period_end: Mapped[date] = mapped_column("period_end", sa.Date, nullable=False)
    decay_unit_days: Mapped[int] = mapped_column(
        "decay_unit_days", sa.Integer, nullable=False, default=1
    )

    # Aggregated resource usage (resource-seconds unit)
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        "resource_usage", ResourceSlotColumn(), nullable=False, default=ResourceSlot
    )

    # Capacity snapshot for normalization
    capacity_snapshot: Mapped[ResourceSlot] = mapped_column(
        "capacity_snapshot",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Scaling group capacity at bucket period. "
        "Sum of agent.available_slots for calculating usage ratio.",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "domain_name",
            "resource_group_id",
            "period_start",
            name="uq_domain_usage_bucket_rg_id",
        ),
        sa.Index("ix_domain_usage_bucket_lookup", "domain_name", "resource_group", "period_start"),
    )


class ProjectUsageBucketRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    """Per-project period-based resource usage aggregation.

    Cache summing all User usage within the project.
    Uses mutable bucket strategy with period_end extension.
    """

    __tablename__ = "project_usage_buckets"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column("project_id", GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        nullable=False,
    )

    # Bucket period information
    period_start: Mapped[date] = mapped_column("period_start", sa.Date, nullable=False)
    period_end: Mapped[date] = mapped_column("period_end", sa.Date, nullable=False)
    decay_unit_days: Mapped[int] = mapped_column(
        "decay_unit_days", sa.Integer, nullable=False, default=1
    )

    # Aggregated resource usage (resource-seconds unit)
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        "resource_usage", ResourceSlotColumn(), nullable=False, default=ResourceSlot
    )

    # Capacity snapshot for normalization
    capacity_snapshot: Mapped[ResourceSlot] = mapped_column(
        "capacity_snapshot",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Scaling group capacity at bucket period. "
        "Sum of agent.available_slots for calculating usage ratio.",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "project_id",
            "resource_group_id",
            "period_start",
            name="uq_project_usage_bucket_rg_id",
        ),
        sa.Index("ix_project_usage_bucket_lookup", "project_id", "resource_group", "period_start"),
    )


class UserUsageBucketRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    """Per-user period-based resource usage aggregation (computation cache).

    Cache aggregating raw data from kernel_usage_records per decay_unit period.
    Since a User can belong to multiple Projects, distinguished by
    (user_uuid, project_id) combination.

    Uses mutable bucket strategy with period_end extension.
    """

    __tablename__ = "user_usage_buckets"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    # User identification (user_uuid + project_id + domain_name combination)
    user_uuid: Mapped[uuid.UUID] = mapped_column("user_uuid", GUID, nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column("project_id", GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False
    )
    resource_group_id: Mapped[ResourceGroupID] = mapped_column(
        "resource_group_id",
        GUID(ResourceGroupID),
        nullable=False,
    )

    # Bucket period information
    period_start: Mapped[date] = mapped_column("period_start", sa.Date, nullable=False)
    period_end: Mapped[date] = mapped_column("period_end", sa.Date, nullable=False)
    decay_unit_days: Mapped[int] = mapped_column(
        "decay_unit_days", sa.Integer, nullable=False, default=1
    )

    # Aggregated resource usage (resource-seconds unit)
    resource_usage: Mapped[ResourceSlot] = mapped_column(
        "resource_usage", ResourceSlotColumn(), nullable=False, default=ResourceSlot
    )

    # Capacity snapshot for normalization
    capacity_snapshot: Mapped[ResourceSlot] = mapped_column(
        "capacity_snapshot",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Scaling group capacity at bucket period. "
        "Sum of agent.available_slots for calculating usage ratio.",
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_uuid",
            "project_id",
            "resource_group_id",
            "period_start",
            name="uq_user_usage_bucket_rg_id",
        ),
        sa.Index(
            "ix_user_usage_bucket_lookup",
            "user_uuid",
            "project_id",
            "resource_group",
            "period_start",
        ),
    )


class UsageBucketEntryRow(Base):  # type: ignore[misc]
    """Per-slot normalized entry for a usage bucket.

    ``resource_usage`` holds resource-seconds (occupied slots integrated over the
    time held), summed per slice.  Unconstrained NUMERIC on purpose: a domain-level
    daily mem bucket reaches ~1e18 byte-seconds, past any fixed precision.

    One entry per (bucket_id, slot_name). ``bucket_type`` discriminates which parent
    table (domain/project/user_usage_buckets) owns it; no FK because references
    span three tables.
    """

    __tablename__ = "usage_bucket_entries"

    bucket_id: Mapped[uuid.UUID] = mapped_column("bucket_id", GUID(), nullable=False)
    bucket_type: Mapped[str] = mapped_column("bucket_type", sa.String(length=16), nullable=False)
    slot_name: Mapped[str] = mapped_column("slot_name", sa.String(length=64), nullable=False)
    resource_usage: Mapped[Decimal] = mapped_column("resource_usage", sa.Numeric(), nullable=False)
    capacity: Mapped[Decimal] = mapped_column(
        "capacity", sa.Numeric(precision=24, scale=6), nullable=False
    )

    __table_args__ = (
        sa.PrimaryKeyConstraint("bucket_id", "slot_name", name="pk_usage_bucket_entries"),
        sa.Index("ix_usage_bucket_entries_slot", "slot_name"),
        sa.Index("ix_usage_bucket_entries_bucket_type", "bucket_type"),
    )
