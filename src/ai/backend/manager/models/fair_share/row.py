"""Fair Share Row models.

Database models for Fair Share state management per resource group:
- DomainFairShareRow: Domain-level fair share state
- ProjectFairShareRow: Project-level fair share state
- UserFairShareRow: User-level fair share state (per project)
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareData,
    FairShareMetadata,
    FairShareSpec,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    ResourceSlotColumn,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.domain import DomainRow
    from ai.backend.manager.models.group import GroupRow
    from ai.backend.manager.models.user import UserRow


__all__ = (
    "DomainFairShareRow",
    "ProjectFairShareRow",
    "UserFairShareRow",
)

# Default values for Fair Share calculation parameters
DEFAULT_HALF_LIFE_DAYS = 7
DEFAULT_LOOKBACK_DAYS = 28
DEFAULT_DECAY_UNIT_DAYS = 1


def _merge_resource_weights(
    row_weights: ResourceSlot,
    default_weight: Decimal,
    available_slots: ResourceSlot,
) -> tuple[ResourceSlot, frozenset[str]]:
    """Merge explicit and default resource weights.

    Args:
        row_weights: Entity's configured weights (may be incomplete)
        default_weight: Scaling group's default weight (single value for all resources)
        available_slots: Available resource types in cluster

    Returns:
        Tuple of (merged_weights, uses_default_resources)
        - merged_weights: Complete ResourceSlot with all available resource types
        - uses_default_resources: Set of resource types using default weight
    """
    merged = {}
    uses_default = []

    for resource_type in available_slots:
        if resource_type in row_weights:
            # Use explicit weight
            merged[resource_type] = row_weights[resource_type]
        else:
            # Use default_weight for all missing resources
            merged[resource_type] = default_weight
            uses_default.append(resource_type)

    return ResourceSlot(merged), frozenset(uses_default)


def _get_domain_fair_share_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return DomainFairShareRow.domain_name == foreign(DomainRow.name)


class DomainFairShareRow(Base):  # type: ignore[misc]
    """Per-domain Fair Share state.

    Stores weight (configured value) and calculated values together for current state.
    One row per (resource_group, domain_name) combination.
    """

    __tablename__ = "domain_fair_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False, index=True
    )
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )

    # Numeric(precision=10, scale=4): Total 10 digits with 4 decimal places.
    # Range: -999999.9999 ~ 999999.9999
    # Example: weight=1.5 means 1.5x priority multiplier compared to default weight=1.0
    # When NULL, the resource group's default_weight should be used.
    weight: Mapped[Decimal | None] = mapped_column(
        "weight",
        sa.Numeric(precision=10, scale=4),
        nullable=True,
        default=None,
        comment="Priority weight multiplier. Higher weight = higher priority allocation ratio. "
        "Example: 2.0 means 2x priority compared to default 1.0. "
        "NULL means use resource group's default_weight.",
    )

    # Numeric(precision=8, scale=6): Total 8 digits with 6 decimal places.
    # Range: 0.000000 ~ 99.999999 (typically 0.0 ~ 1.0)
    # Calculated using formula: F = 2^(-normalized_usage / weight)
    fair_share_factor: Mapped[Decimal] = mapped_column(
        "fair_share_factor",
        sa.Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("1.0"),
        comment="Calculated priority score from 0.0 to 1.0. "
        "Higher value = less past usage = higher scheduling priority. "
        "Formula: F = 2^(-normalized_usage / weight)",
    )
    total_decayed_usage: Mapped[ResourceSlot] = mapped_column(
        "total_decayed_usage",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Sum of historical resource usage with time decay applied. "
        "Unit: resource-seconds (e.g., cpu-seconds, mem-seconds). "
        "Older usage is weighted less via half-life decay.",
    )
    resource_weights: Mapped[ResourceSlot] = mapped_column(
        "resource_weights",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Resource weights used in fair share calculation. "
        "From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}",
    )
    # Numeric(precision=8, scale=6): Total 8 digits with 6 decimal places.
    # Range: 0.000000 ~ 99.999999 (typically 0.0 ~ 1.0)
    # IMPORTANT: Both usage and capacity must be in resource-seconds for correct ratio.
    # - usage: resource-seconds (e.g., 3600 GPU-seconds = 1 GPU-hour)
    # - capacity: resource-seconds (e.g., 8 GPUs × 86400 sec/day × 28 days)
    # DO NOT mix resource-seconds (usage) with raw resource units (capacity).
    normalized_usage: Mapped[Decimal] = mapped_column(
        "normalized_usage",
        sa.Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("0"),
        comment="Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). "
        "Both usage and capacity are in resource-seconds. "
        "Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])",
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        "last_calculated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        comment="Timestamp when fair_share_factor was last recalculated by batch job.",
    )

    lookback_start: Mapped[date] = mapped_column(
        "lookback_start",
        sa.Date,
        nullable=False,
        server_default=sa.func.current_date(),
        comment="Start date of the usage history window used in last calculation. "
        "Typically: today - lookback_days.",
    )
    lookback_end: Mapped[date] = mapped_column(
        "lookback_end",
        sa.Date,
        nullable=False,
        server_default=sa.func.current_date(),
        comment="End date of the usage history window used in last calculation. Typically: today.",
    )
    half_life_days: Mapped[int] = mapped_column(
        "half_life_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_HALF_LIFE_DAYS,
        comment="Number of days for usage to decay to 50%%. "
        "Example: 7 means usage from 7 days ago counts as 50%% of recent usage.",
    )
    lookback_days: Mapped[int] = mapped_column(
        "lookback_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_LOOKBACK_DAYS,
        comment="Number of days of usage history to consider for fair share calculation. "
        "Example: 28 means only last 28 days of usage affects priority.",
    )
    decay_unit_days: Mapped[int] = mapped_column(
        "decay_unit_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_DECAY_UNIT_DAYS,
        comment="Aggregation period for usage buckets in days. "
        "Example: 1 means daily aggregation, 7 means weekly aggregation.",
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

    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_domain_fair_share_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.UniqueConstraint("resource_group", "domain_name", name="uq_domain_fair_share"),
        sa.Index("ix_domain_fair_share_lookup", "resource_group", "domain_name"),
    )

    def to_data(
        self,
        default_weight: Decimal,
        available_slots: ResourceSlot,
    ) -> DomainFairShareData:
        """Convert to DomainFairShareData with merged resource weights.

        Args:
            default_weight: Scaling group's default weight (used when self.weight is NULL
                           and as fallback for missing resource weights)
            available_slots: Available resource types in the cluster

        Note: self.weight can be NULL in DB.
        - NULL means "use default weight" (use_default=True)
        - NOT NULL means "explicit weight" (use_default=False)
        """
        # Handle entity weight (existing logic)
        if self.weight is None:
            weight = default_weight
            use_default = True
        else:
            weight = self.weight
            use_default = False

        # Merge resource weights (new)
        merged_weights, uses_default_resources = _merge_resource_weights(
            self.resource_weights,
            default_weight,
            available_slots,
        )

        return DomainFairShareData(
            resource_group=self.resource_group,
            domain_name=self.domain_name,
            data=FairShareData(
                spec=FairShareSpec(
                    weight=weight,
                    half_life_days=self.half_life_days,
                    lookback_days=self.lookback_days,
                    decay_unit_days=self.decay_unit_days,
                    resource_weights=merged_weights,  # Use merged weights
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=self.fair_share_factor,
                    total_decayed_usage=self.total_decayed_usage,
                    normalized_usage=self.normalized_usage,
                    lookback_start=self.lookback_start,
                    lookback_end=self.lookback_end,
                    last_calculated_at=self.last_calculated_at,
                ),
                metadata=FairShareMetadata(
                    created_at=self.created_at,
                    updated_at=self.updated_at,
                ),
                use_default=use_default,  # True if weight was NULL
                uses_default_resources=uses_default_resources,  # New field
            ),
        )


def _get_project_fair_share_project_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.group import GroupRow

    return ProjectFairShareRow.project_id == foreign(GroupRow.id)


def _get_project_fair_share_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return ProjectFairShareRow.domain_name == foreign(DomainRow.name)


class ProjectFairShareRow(Base):  # type: ignore[misc]
    """Per-project Fair Share state.

    One row per (resource_group, project_id) combination.
    """

    __tablename__ = "project_fair_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column("project_id", GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )

    weight: Mapped[Decimal | None] = mapped_column(
        "weight",
        sa.Numeric(precision=10, scale=4),
        nullable=True,
        default=None,
        comment="Priority weight multiplier. Higher weight = higher priority allocation ratio. "
        "Example: 2.0 means 2x priority compared to default 1.0. "
        "NULL means use resource group's default_weight.",
    )

    fair_share_factor: Mapped[Decimal] = mapped_column(
        "fair_share_factor",
        sa.Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("1.0"),
        comment="Calculated priority score from 0.0 to 1.0. "
        "Higher value = less past usage = higher scheduling priority. "
        "Formula: F = 2^(-normalized_usage / weight)",
    )
    total_decayed_usage: Mapped[ResourceSlot] = mapped_column(
        "total_decayed_usage",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Sum of historical resource usage with time decay applied. Unit: resource-seconds.",
    )
    resource_weights: Mapped[ResourceSlot] = mapped_column(
        "resource_weights",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Resource weights used in fair share calculation. "
        "From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}",
    )
    # IMPORTANT: Both usage and capacity must be in resource-seconds for correct ratio.
    # - usage: resource-seconds (e.g., 3600 GPU-seconds = 1 GPU-hour)
    # - capacity: resource-seconds (e.g., 8 GPUs × 86400 sec/day × 28 days)
    # DO NOT mix resource-seconds (usage) with raw resource units (capacity).
    normalized_usage: Mapped[Decimal] = mapped_column(
        "normalized_usage",
        sa.Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("0"),
        comment="Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). "
        "Both usage and capacity are in resource-seconds. "
        "Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])",
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        "last_calculated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        comment="Timestamp when fair_share_factor was last recalculated.",
    )

    lookback_start: Mapped[date] = mapped_column(
        "lookback_start",
        sa.Date,
        nullable=False,
        server_default=sa.func.current_date(),
        comment="Start date of the usage history window used in last calculation.",
    )
    lookback_end: Mapped[date] = mapped_column(
        "lookback_end",
        sa.Date,
        nullable=False,
        server_default=sa.func.current_date(),
        comment="End date of the usage history window used in last calculation.",
    )
    half_life_days: Mapped[int] = mapped_column(
        "half_life_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_HALF_LIFE_DAYS,
        comment="Number of days for usage to decay to 50%%.",
    )
    lookback_days: Mapped[int] = mapped_column(
        "lookback_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_LOOKBACK_DAYS,
        comment="Number of days of usage history to consider.",
    )
    decay_unit_days: Mapped[int] = mapped_column(
        "decay_unit_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_DECAY_UNIT_DAYS,
        comment="Aggregation period for usage buckets in days.",
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

    project: Mapped[GroupRow | None] = relationship(
        "GroupRow",
        primaryjoin=_get_project_fair_share_project_join_condition,
        foreign_keys=[project_id],
        uselist=False,
        viewonly=True,
    )
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_project_fair_share_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.UniqueConstraint("resource_group", "project_id", name="uq_project_fair_share"),
        sa.Index("ix_project_fair_share_lookup", "resource_group", "project_id"),
    )

    def to_data(
        self,
        default_weight: Decimal,
        available_slots: ResourceSlot,
    ) -> ProjectFairShareData:
        """Convert to ProjectFairShareData with merged resource weights.

        Args:
            default_weight: Scaling group's default weight (used when self.weight is NULL
                           and as fallback for missing resource weights)
            available_slots: Available resource types in the cluster

        Note: self.weight can be NULL in DB.
        - NULL means "use default weight" (use_default=True)
        - NOT NULL means "explicit weight" (use_default=False)
        """
        # Handle entity weight (existing logic)
        if self.weight is None:
            weight = default_weight
            use_default = True
        else:
            weight = self.weight
            use_default = False

        # Merge resource weights (new)
        merged_weights, uses_default_resources = _merge_resource_weights(
            self.resource_weights,
            default_weight,
            available_slots,
        )

        return ProjectFairShareData(
            resource_group=self.resource_group,
            project_id=self.project_id,
            domain_name=self.domain_name,
            data=FairShareData(
                spec=FairShareSpec(
                    weight=weight,
                    half_life_days=self.half_life_days,
                    lookback_days=self.lookback_days,
                    decay_unit_days=self.decay_unit_days,
                    resource_weights=merged_weights,  # Use merged weights
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=self.fair_share_factor,
                    total_decayed_usage=self.total_decayed_usage,
                    normalized_usage=self.normalized_usage,
                    lookback_start=self.lookback_start,
                    lookback_end=self.lookback_end,
                    last_calculated_at=self.last_calculated_at,
                ),
                metadata=FairShareMetadata(
                    created_at=self.created_at,
                    updated_at=self.updated_at,
                ),
                use_default=use_default,  # True if weight was NULL
                uses_default_resources=uses_default_resources,  # New field
            ),
        )


def _get_user_fair_share_user_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.user import UserRow

    return UserFairShareRow.user_uuid == foreign(UserRow.uuid)


def _get_user_fair_share_project_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.group import GroupRow

    return UserFairShareRow.project_id == foreign(GroupRow.id)


def _get_user_fair_share_domain_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.domain import DomainRow

    return UserFairShareRow.domain_name == foreign(DomainRow.name)


class UserFairShareRow(Base):  # type: ignore[misc]
    """Per-user Fair Share state.

    Since a User can belong to multiple Projects, distinguished by
    (user_uuid, project_id) combination.

    One row per (resource_group, user_uuid, project_id) combination.
    """

    __tablename__ = "user_fair_shares"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    resource_group: Mapped[str] = mapped_column(
        "resource_group", sa.String(length=64), nullable=False, index=True
    )
    user_uuid: Mapped[uuid.UUID] = mapped_column("user_uuid", GUID, nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column("project_id", GUID, nullable=False, index=True)
    domain_name: Mapped[str] = mapped_column(
        "domain_name", sa.String(length=64), nullable=False, index=True
    )

    weight: Mapped[Decimal | None] = mapped_column(
        "weight",
        sa.Numeric(precision=10, scale=4),
        nullable=True,
        default=None,
        comment="Priority weight multiplier. Higher weight = higher priority allocation ratio. "
        "Example: 2.0 means 2x priority compared to default 1.0. "
        "NULL means use resource group's default_weight.",
    )

    fair_share_factor: Mapped[Decimal] = mapped_column(
        "fair_share_factor",
        sa.Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("1.0"),
        comment="Calculated priority score from 0.0 to 1.0. "
        "Higher value = less past usage = higher scheduling priority. "
        "Formula: F = 2^(-normalized_usage / weight)",
    )
    scheduling_rank: Mapped[int | None] = mapped_column(
        "scheduling_rank",
        sa.Integer,
        nullable=True,
        comment="Computed scheduling priority rank. "
        "Lower value = higher priority (1 = highest). "
        "NULL means rank calculation has not been performed yet.",
    )
    total_decayed_usage: Mapped[ResourceSlot] = mapped_column(
        "total_decayed_usage",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Sum of historical resource usage with time decay applied. Unit: resource-seconds.",
    )
    resource_weights: Mapped[ResourceSlot] = mapped_column(
        "resource_weights",
        ResourceSlotColumn(),
        nullable=False,
        default=ResourceSlot,
        comment="Resource weights used in fair share calculation. "
        "From scheduler_opts. Example: {cpu: 1.0, mem: 1.0, cuda.device: 10.0}",
    )
    # IMPORTANT: Both usage and capacity must be in resource-seconds for correct ratio.
    # - usage: resource-seconds (e.g., 3600 GPU-seconds = 1 GPU-hour)
    # - capacity: resource-seconds (e.g., 8 GPUs × 86400 sec/day × 28 days)
    # DO NOT mix resource-seconds (usage) with raw resource units (capacity).
    normalized_usage: Mapped[Decimal] = mapped_column(
        "normalized_usage",
        sa.Numeric(precision=8, scale=6),
        nullable=False,
        default=Decimal("0"),
        comment="Weighted average of (usage/capacity) per resource (0.0 ~ 1.0). "
        "Both usage and capacity are in resource-seconds. "
        "Formula: sum((usage[r]/capacity[r]) * weight[r]) / sum(weight[r])",
    )
    last_calculated_at: Mapped[datetime] = mapped_column(
        "last_calculated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        comment="Timestamp when fair_share_factor was last recalculated.",
    )

    lookback_start: Mapped[date] = mapped_column(
        "lookback_start",
        sa.Date,
        nullable=False,
        server_default=sa.func.current_date(),
        comment="Start date of the usage history window used in last calculation.",
    )
    lookback_end: Mapped[date] = mapped_column(
        "lookback_end",
        sa.Date,
        nullable=False,
        server_default=sa.func.current_date(),
        comment="End date of the usage history window used in last calculation.",
    )
    half_life_days: Mapped[int] = mapped_column(
        "half_life_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_HALF_LIFE_DAYS,
        comment="Number of days for usage to decay to 50%%.",
    )
    lookback_days: Mapped[int] = mapped_column(
        "lookback_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_LOOKBACK_DAYS,
        comment="Number of days of usage history to consider.",
    )
    decay_unit_days: Mapped[int] = mapped_column(
        "decay_unit_days",
        sa.Integer,
        nullable=False,
        default=DEFAULT_DECAY_UNIT_DAYS,
        comment="Aggregation period for usage buckets in days.",
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

    user: Mapped[UserRow | None] = relationship(
        "UserRow",
        primaryjoin=_get_user_fair_share_user_join_condition,
        foreign_keys=[user_uuid],
        uselist=False,
        viewonly=True,
    )
    project: Mapped[GroupRow | None] = relationship(
        "GroupRow",
        primaryjoin=_get_user_fair_share_project_join_condition,
        foreign_keys=[project_id],
        uselist=False,
        viewonly=True,
    )
    domain: Mapped[DomainRow | None] = relationship(
        "DomainRow",
        primaryjoin=_get_user_fair_share_domain_join_condition,
        foreign_keys=[domain_name],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "resource_group",
            "user_uuid",
            "project_id",
            name="uq_user_fair_share",
        ),
        sa.Index("ix_user_fair_share_lookup", "resource_group", "user_uuid", "project_id"),
    )

    def to_data(
        self,
        default_weight: Decimal,
        available_slots: ResourceSlot,
    ) -> UserFairShareData:
        """Convert to UserFairShareData with merged resource weights.

        Args:
            default_weight: Scaling group's default weight (used when self.weight is NULL
                           and as fallback for missing resource weights)
            available_slots: Available resource types in the cluster

        Note: self.weight can be NULL in DB.
        - NULL means "use default weight" (use_default=True)
        - NOT NULL means "explicit weight" (use_default=False)
        """
        # Handle entity weight (existing logic)
        if self.weight is None:
            weight = default_weight
            use_default = True
        else:
            weight = self.weight
            use_default = False

        # Merge resource weights (new)
        merged_weights, uses_default_resources = _merge_resource_weights(
            self.resource_weights,
            default_weight,
            available_slots,
        )

        return UserFairShareData(
            resource_group=self.resource_group,
            user_uuid=self.user_uuid,
            project_id=self.project_id,
            domain_name=self.domain_name,
            data=FairShareData(
                spec=FairShareSpec(
                    weight=weight,
                    half_life_days=self.half_life_days,
                    lookback_days=self.lookback_days,
                    decay_unit_days=self.decay_unit_days,
                    resource_weights=merged_weights,  # Use merged weights
                ),
                calculation_snapshot=FairShareCalculationSnapshot(
                    fair_share_factor=self.fair_share_factor,
                    total_decayed_usage=self.total_decayed_usage,
                    normalized_usage=self.normalized_usage,
                    lookback_start=self.lookback_start,
                    lookback_end=self.lookback_end,
                    last_calculated_at=self.last_calculated_at,
                ),
                metadata=FairShareMetadata(
                    created_at=self.created_at,
                    updated_at=self.updated_at,
                ),
                use_default=use_default,  # True if weight was NULL
                uses_default_resources=uses_default_resources,  # New field
            ),
            scheduling_rank=self.scheduling_rank,
        )
