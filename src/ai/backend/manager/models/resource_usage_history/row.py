"""Resource Usage History Row models.

This module defines the database models for tracking resource usage history:

Tier 1 - Raw Data:
- KernelUsageRecordRow: Per-period kernel resource usage records

Tier 2 - Aggregation Cache:
- DomainUsageBucketRow: Domain-level period aggregation
- ProjectUsageBucketRow: Project-level period aggregation
- UserUsageBucketRow: User-level period aggregation (per project)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.models.base import (
    GUID,
    Base,
    ResourceSlotColumn,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.domain import DomainRow
    from ai.backend.manager.models.group import GroupRow
    from ai.backend.manager.models.kernel import KernelRow
    from ai.backend.manager.models.session import SessionRow
    from ai.backend.manager.models.user import UserRow


__all__ = (
    "KernelUsageRecordRow",
    "DomainUsageBucketRow",
    "ProjectUsageBucketRow",
    "UserUsageBucketRow",
)


def _get_kernel_usage_record_kernel_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.kernel import KernelRow

    return KernelUsageRecordRow.kernel_id == foreign(KernelRow.id)


def _get_kernel_usage_record_session_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.session import SessionRow

    return KernelUsageRecordRow.session_id == foreign(SessionRow.id)


def _get_kernel_usage_record_user_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.user import UserRow

    return KernelUsageRecordRow.user_uuid == foreign(UserRow.uuid)


def _get_kernel_usage_record_project_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.group import GroupRow

    return KernelUsageRecordRow.project_id == foreign(GroupRow.id)


def _get_kernel_usage_record_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return KernelUsageRecordRow.domain_name == foreign(DomainRow.name)


class KernelUsageRecordRow(Base):
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

    # Relationships (Optional since referenced entities can be deleted)
    kernel: Mapped[KernelRow | None] = relationship(
        "KernelRow",
        primaryjoin=_get_kernel_usage_record_kernel_join_condition,
        foreign_keys=[kernel_id],
        uselist=False,
        viewonly=True,
    )
    session: Mapped[SessionRow | None] = relationship(
        "SessionRow",
        primaryjoin=_get_kernel_usage_record_session_join_condition,
        foreign_keys=[session_id],
        uselist=False,
        viewonly=True,
    )
    user: Mapped[UserRow | None] = relationship(
        "UserRow",
        primaryjoin=_get_kernel_usage_record_user_join_condition,
        foreign_keys=[user_uuid],
        uselist=False,
        viewonly=True,
    )
    project: Mapped[GroupRow | None] = relationship(
        "GroupRow",
        primaryjoin=_get_kernel_usage_record_project_join_condition,
        foreign_keys=[project_id],
        uselist=False,
        viewonly=True,
    )
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_kernel_usage_record_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.Index("ix_kernel_usage_sg_period", "resource_group", "period_start"),
        sa.Index("ix_kernel_usage_user_period", "user_uuid", "period_start"),
    )


def _get_domain_usage_bucket_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return DomainUsageBucketRow.domain_name == foreign(DomainRow.name)


class DomainUsageBucketRow(Base):
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

    # Metadata
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

    # Relationships
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_domain_usage_bucket_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "domain_name",
            "resource_group",
            "period_start",
            name="uq_domain_usage_bucket",
        ),
        sa.Index("ix_domain_usage_bucket_lookup", "domain_name", "resource_group", "period_start"),
    )


def _get_project_usage_bucket_project_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.group import GroupRow

    return ProjectUsageBucketRow.project_id == foreign(GroupRow.id)


def _get_project_usage_bucket_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return ProjectUsageBucketRow.domain_name == foreign(DomainRow.name)


class ProjectUsageBucketRow(Base):
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

    # Metadata
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

    # Relationships
    project: Mapped[GroupRow | None] = relationship(
        "GroupRow",
        primaryjoin=_get_project_usage_bucket_project_join_condition,
        foreign_keys=[project_id],
        uselist=False,
        viewonly=True,
    )
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_project_usage_bucket_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "project_id",
            "resource_group",
            "period_start",
            name="uq_project_usage_bucket",
        ),
        sa.Index("ix_project_usage_bucket_lookup", "project_id", "resource_group", "period_start"),
    )


def _get_user_usage_bucket_user_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.user import UserRow

    return UserUsageBucketRow.user_uuid == foreign(UserRow.uuid)


def _get_user_usage_bucket_project_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.group import GroupRow

    return UserUsageBucketRow.project_id == foreign(GroupRow.id)


def _get_user_usage_bucket_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return UserUsageBucketRow.domain_name == foreign(DomainRow.name)


class UserUsageBucketRow(Base):
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

    # Metadata
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

    # Relationships
    user: Mapped[UserRow | None] = relationship(
        "UserRow",
        primaryjoin=_get_user_usage_bucket_user_join_condition,
        foreign_keys=[user_uuid],
        uselist=False,
        viewonly=True,
    )
    project: Mapped[GroupRow | None] = relationship(
        "GroupRow",
        primaryjoin=_get_user_usage_bucket_project_join_condition,
        foreign_keys=[project_id],
        uselist=False,
        viewonly=True,
    )
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_user_usage_bucket_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_uuid",
            "project_id",
            "resource_group",
            "period_start",
            name="uq_user_usage_bucket",
        ),
        sa.Index(
            "ix_user_usage_bucket_lookup",
            "user_uuid",
            "project_id",
            "resource_group",
            "period_start",
        ),
    )
