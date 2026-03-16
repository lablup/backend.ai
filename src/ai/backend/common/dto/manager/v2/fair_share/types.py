"""
Common types for fair_share DTO v2.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    # Enums
    "OrderDirection",
    "DomainFairShareOrderField",
    "ProjectFairShareOrderField",
    "UserFairShareOrderField",
    "DomainUsageBucketOrderField",
    "ProjectUsageBucketOrderField",
    "UserUsageBucketOrderField",
    # Sub-models
    "ResourceSlotEntryInfo",
    "ResourceSlotInfo",
    "FairShareSpecInfo",
    "FairShareCalculationSnapshotInfo",
    "UsageBucketMetadataInfo",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class DomainFairShareOrderField(StrEnum):
    """Fields available for ordering domain fair shares."""

    FAIR_SHARE_FACTOR = "fair_share_factor"
    DOMAIN_NAME = "domain_name"
    CREATED_AT = "created_at"


class ProjectFairShareOrderField(StrEnum):
    """Fields available for ordering project fair shares."""

    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"


class UserFairShareOrderField(StrEnum):
    """Fields available for ordering user fair shares."""

    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"


class DomainUsageBucketOrderField(StrEnum):
    """Fields available for ordering domain usage buckets."""

    PERIOD_START = "period_start"


class ProjectUsageBucketOrderField(StrEnum):
    """Fields available for ordering project usage buckets."""

    PERIOD_START = "period_start"


class UserUsageBucketOrderField(StrEnum):
    """Fields available for ordering user usage buckets."""

    PERIOD_START = "period_start"


class ResourceSlotEntryInfo(BaseResponseModel):
    """A single resource slot entry with resource type and quantity."""

    resource_type: str = Field(description="Resource type identifier (e.g., cpu, mem, cuda.shares)")
    quantity: str = Field(description="Quantity as a decimal string to preserve precision")


class ResourceSlotInfo(BaseResponseModel):
    """Collection of compute resource allocations."""

    entries: list[ResourceSlotEntryInfo] = Field(description="List of resource allocations")


class FairShareSpecInfo(BaseResponseModel):
    """Fair share specification parameters."""

    weight: Decimal | None = Field(
        default=None,
        description=(
            "Base weight for this entity. None means use resource group's default_weight."
        ),
    )
    half_life_days: int = Field(description="Half-life for exponential decay in days")
    lookback_days: int = Field(description="Total lookback period in days")
    decay_unit_days: int = Field(description="Granularity of decay buckets in days")
    resource_weights: ResourceSlotInfo = Field(description="Weights for each resource type")


class FairShareCalculationSnapshotInfo(BaseResponseModel):
    """Snapshot of the most recent fair share calculation."""

    fair_share_factor: Decimal = Field(description="Computed fair share factor (0-1 range)")
    total_decayed_usage: ResourceSlotInfo = Field(description="Sum of decayed historical usage")
    normalized_usage: Decimal = Field(description="Single scalar representing weighted consumption")
    lookback_start: date = Field(description="Start date of the lookback window")
    lookback_end: date = Field(description="End date of the lookback window")
    last_calculated_at: datetime = Field(description="Timestamp when calculation was performed")


class UsageBucketMetadataInfo(BaseResponseModel):
    """Common metadata for usage bucket records."""

    period_start: date = Field(description="Start date of the usage measurement period (inclusive)")
    period_end: date = Field(description="End date of the usage measurement period (exclusive)")
    decay_unit_days: int = Field(description="Number of days in each decay unit for this bucket")
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")
    average_daily_usage: ResourceSlotInfo = Field(
        description="Average daily resource usage during this period"
    )
    usage_capacity_ratio: ResourceSlotInfo = Field(
        description="Ratio of usage to capacity (usage / total capacity available)"
    )
