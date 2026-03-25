"""
Common types for fair_share DTO v2.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection

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
    "ResourceWeightEntryInfo",
    "FairShareSpecInfo",
    "FairShareCalculationSnapshotInfo",
    "UsageBucketMetadataInfo",
    # Scope DTOs
    "ResourceGroupDomainScopeDTO",
    "ResourceGroupProjectScopeDTO",
    "ResourceGroupUserScopeDTO",
    "DomainFairShareScopeDTO",
    "ProjectFairShareScopeDTO",
    "UserFairShareScopeDTO",
    "ProjectUsageScopeDTO",
    "DomainUsageScopeDTO",
    "UserUsageScopeDTO",
    "DomainUsageBucketScopeDTO",
    "ProjectUsageBucketScopeDTO",
    "UserUsageBucketScopeDTO",
)


class DomainFairShareOrderField(StrEnum):
    """Fields available for ordering domain fair shares."""

    FAIR_SHARE_FACTOR = "fair_share_factor"
    DOMAIN_NAME = "domain_name"
    CREATED_AT = "created_at"
    DOMAIN_IS_ACTIVE = "domain_is_active"


class ProjectFairShareOrderField(StrEnum):
    """Fields available for ordering project fair shares."""

    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"
    PROJECT_NAME = "project_name"
    PROJECT_IS_ACTIVE = "project_is_active"


class UserFairShareOrderField(StrEnum):
    """Fields available for ordering user fair shares."""

    FAIR_SHARE_FACTOR = "fair_share_factor"
    CREATED_AT = "created_at"
    USER_USERNAME = "user_username"
    USER_EMAIL = "user_email"


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
    quantity: Decimal = Field(description="Quantity of the resource")


class ResourceSlotInfo(BaseResponseModel):
    """Collection of compute resource allocations."""

    entries: list[ResourceSlotEntryInfo] = Field(description="List of resource allocations")


class ResourceWeightEntryInfo(BaseResponseModel):
    """A single resource weight entry with default indicator."""

    resource_type: str = Field(description="Resource type identifier")
    weight: Decimal = Field(description="Weight multiplier for this resource type")
    uses_default: bool = Field(
        description="Whether this resource uses the resource group's default weight"
    )


class FairShareSpecInfo(BaseResponseModel):
    """Fair share specification parameters."""

    weight: Decimal = Field(
        description=(
            "Effective weight for this entity. Always the resolved value "
            "(either the explicitly set weight or the resource group's default_weight)."
        ),
    )
    uses_default: bool = Field(
        default=False,
        description=(
            "Whether this entity uses the resource group's default_weight. "
            "True means no explicit weight was set."
        ),
    )
    half_life_days: int = Field(description="Half-life for exponential decay in days")
    lookback_days: int = Field(description="Total lookback period in days")
    decay_unit_days: int = Field(description="Granularity of decay buckets in days")
    resource_weights: list[ResourceWeightEntryInfo] = Field(
        description="Weights for each resource type with default indicators"
    )


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


# Scope DTOs for resource group and usage bucket scoped APIs


class DomainFairShareScopeDTO(BaseRequestModel):
    """Scope for domain fair share queries within a resource group."""

    resource_group_name: str = Field(description="Resource group to filter fair shares by.")


class ProjectFairShareScopeDTO(BaseRequestModel):
    """Scope for project fair share queries within a resource group."""

    resource_group_name: str = Field(description="Resource group to filter fair shares by.")


class UserFairShareScopeDTO(BaseRequestModel):
    """Scope for user fair share queries within a resource group."""

    resource_group_name: str = Field(description="Resource group to filter fair shares by.")


class DomainUsageScopeDTO(BaseRequestModel):
    """Scope for domain usage bucket queries within a resource group (node-level context)."""

    resource_group_name: str = Field(description="Resource group to filter usage buckets by.")


class ProjectUsageScopeDTO(BaseRequestModel):
    """Scope for project usage bucket queries within a resource group (node-level context)."""

    resource_group_name: str = Field(description="Resource group to filter usage buckets by.")


class UserUsageScopeDTO(BaseRequestModel):
    """Scope for user usage bucket queries within a resource group (node-level context)."""

    resource_group_name: str = Field(description="Resource group to filter usage buckets by.")


class ResourceGroupDomainScopeDTO(BaseRequestModel):
    """Scope for domain-level APIs within a resource group context."""

    resource_group_name: str = Field(description="Resource group name to scope the operation.")


class ResourceGroupProjectScopeDTO(BaseRequestModel):
    """Scope for project-level APIs within a resource group and domain context."""

    resource_group_name: str = Field(description="Resource group name to scope the operation.")
    domain_name: str = Field(description="Domain name to scope the operation.")


class ResourceGroupUserScopeDTO(BaseRequestModel):
    """Scope for user-level APIs within a resource group, domain, and project context."""

    resource_group_name: str = Field(description="Resource group name to scope the operation.")
    domain_name: str = Field(description="Domain name to scope the operation.")
    project_id: str = Field(description="Project ID to scope the operation.")


class DomainUsageBucketScopeDTO(BaseRequestModel):
    """Scope for domain-level usage bucket APIs."""

    resource_group_name: str = Field(description="Resource group name.")
    domain_name: str = Field(description="Domain name to retrieve usage buckets for.")


class ProjectUsageBucketScopeDTO(BaseRequestModel):
    """Scope for project-level usage bucket APIs."""

    resource_group_name: str = Field(description="Resource group name.")
    domain_name: str = Field(description="Domain name.")
    project_id: str = Field(description="Project ID (will be converted to UUID).")


class UserUsageBucketScopeDTO(BaseRequestModel):
    """Scope for user-level usage bucket APIs."""

    resource_group_name: str = Field(description="Resource group name.")
    domain_name: str = Field(description="Domain name.")
    project_id: str = Field(description="Project ID (will be converted to UUID).")
    user_uuid: str = Field(description="User UUID (will be converted to UUID).")
