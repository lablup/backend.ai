"""Response DTOs for Fair Share API."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    # Common
    "PaginationInfo",
    "ResourceSlotEntryDTO",
    "ResourceSlotDTO",
    "FairShareSpecDTO",
    "FairShareCalculationSnapshotDTO",
    # Domain Fair Share
    "DomainFairShareDTO",
    "GetDomainFairShareResponse",
    "SearchDomainFairSharesResponse",
    "UpsertDomainFairShareWeightResponse",
    "BulkUpsertDomainFairShareWeightResponse",
    # Project Fair Share
    "ProjectFairShareDTO",
    "GetProjectFairShareResponse",
    "SearchProjectFairSharesResponse",
    "UpsertProjectFairShareWeightResponse",
    "BulkUpsertProjectFairShareWeightResponse",
    # User Fair Share
    "UserFairShareDTO",
    "GetUserFairShareResponse",
    "SearchUserFairSharesResponse",
    "UpsertUserFairShareWeightResponse",
    "BulkUpsertUserFairShareWeightResponse",
    # Domain Usage Bucket
    "UsageBucketMetadataDTO",
    "DomainUsageBucketDTO",
    "SearchDomainUsageBucketsResponse",
    # Project Usage Bucket
    "ProjectUsageBucketDTO",
    "SearchProjectUsageBucketsResponse",
    # User Usage Bucket
    "UserUsageBucketDTO",
    "SearchUserUsageBucketsResponse",
    # Resource Group Fair Share Spec
    "ResourceGroupFairShareSpecDTO",
    "UpdateResourceGroupFairShareSpecResponse",
)


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class ResourceSlotEntryDTO(BaseModel):
    """A single resource slot entry with resource type and quantity."""

    resource_type: str = Field(description="Resource type identifier (e.g., cpu, mem, cuda.shares)")
    quantity: str = Field(description="Quantity as a decimal string to preserve precision")


class ResourceSlotDTO(BaseModel):
    """Collection of compute resource allocations."""

    entries: list[ResourceSlotEntryDTO] = Field(description="List of resource allocations")


class FairShareSpecDTO(BaseModel):
    """Fair share specification parameters."""

    weight: Decimal | None = Field(
        default=None,
        description="Base weight for this entity. None means use resource group's default_weight.",
    )
    half_life_days: int = Field(description="Half-life for exponential decay in days")
    lookback_days: int = Field(description="Total lookback period in days")
    decay_unit_days: int = Field(description="Granularity of decay buckets in days")
    resource_weights: ResourceSlotDTO = Field(description="Weights for each resource type")


class FairShareCalculationSnapshotDTO(BaseModel):
    """Snapshot of the most recent fair share calculation."""

    fair_share_factor: Decimal = Field(description="Computed fair share factor (0-1 range)")
    total_decayed_usage: ResourceSlotDTO = Field(description="Sum of decayed historical usage")
    normalized_usage: Decimal = Field(description="Single scalar representing weighted consumption")
    lookback_start: date = Field(description="Start date of the lookback window")
    lookback_end: date = Field(description="End date of the lookback window")
    last_calculated_at: datetime = Field(description="Timestamp when calculation was performed")


# Domain Fair Share


class DomainFairShareDTO(BaseResponseModel):
    """
    Domain-level fair share data representing scheduling priority for an entire domain.

    The fair share factor determines how resources are allocated to a domain relative to
    other domains within the same scaling group. A lower factor indicates higher priority.
    """

    id: UUID = Field(description="Unique identifier for this fair share record")
    resource_group: str = Field(description="Name of the scaling group this fair share belongs to")
    domain_name: str = Field(description="Name of the domain this fair share is calculated for")
    spec: FairShareSpecDTO = Field(
        description="Fair share specification parameters used for calculation"
    )
    calculation_snapshot: FairShareCalculationSnapshotDTO = Field(
        description="Snapshot of the most recent fair share calculation results"
    )
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")


class GetDomainFairShareResponse(BaseResponseModel):
    """Response for getting a single domain fair share."""

    item: DomainFairShareDTO | None = Field(default=None, description="Domain fair share data")


class SearchDomainFairSharesResponse(BaseResponseModel):
    """Response for listing domain fair shares."""

    items: list[DomainFairShareDTO] = Field(description="List of domain fair shares")
    pagination: PaginationInfo = Field(description="Pagination information")


# Project Fair Share


class ProjectFairShareDTO(BaseResponseModel):
    """
    Project-level fair share data representing scheduling priority for a specific project.

    The fair share factor determines how resources are allocated to a project relative to
    other projects within the same domain and scaling group. A lower factor indicates higher priority.
    """

    id: UUID = Field(description="Unique identifier for this fair share record")
    resource_group: str = Field(description="Name of the scaling group this fair share belongs to")
    project_id: UUID = Field(description="UUID of the project this fair share is calculated for")
    domain_name: str = Field(description="Name of the domain the project belongs to")
    spec: FairShareSpecDTO = Field(
        description="Fair share specification parameters used for calculation"
    )
    calculation_snapshot: FairShareCalculationSnapshotDTO = Field(
        description="Snapshot of the most recent fair share calculation results"
    )
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")


class GetProjectFairShareResponse(BaseResponseModel):
    """Response for getting a single project fair share."""

    item: ProjectFairShareDTO | None = Field(default=None, description="Project fair share data")


class SearchProjectFairSharesResponse(BaseResponseModel):
    """Response for listing project fair shares."""

    items: list[ProjectFairShareDTO] = Field(description="List of project fair shares")
    pagination: PaginationInfo = Field(description="Pagination information")


# User Fair Share


class UserFairShareDTO(BaseResponseModel):
    """
    User-level fair share data representing scheduling priority for an individual user.

    The fair share factor determines how resources are allocated to a user relative to
    other users within the same project and scaling group. A lower factor indicates higher priority.
    This is the most granular level of fair share calculation.
    """

    id: UUID = Field(description="Unique identifier for this fair share record")
    resource_group: str = Field(description="Name of the scaling group this fair share belongs to")
    user_uuid: UUID = Field(description="UUID of the user this fair share is calculated for")
    project_id: UUID = Field(description="UUID of the project the user belongs to")
    domain_name: str = Field(description="Name of the domain the user belongs to")
    spec: FairShareSpecDTO = Field(
        description="Fair share specification parameters used for calculation"
    )
    calculation_snapshot: FairShareCalculationSnapshotDTO = Field(
        description="Snapshot of the most recent fair share calculation results"
    )
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")


class GetUserFairShareResponse(BaseResponseModel):
    """Response for getting a single user fair share."""

    item: UserFairShareDTO | None = Field(default=None, description="User fair share data")


class SearchUserFairSharesResponse(BaseResponseModel):
    """Response for listing user fair shares."""

    items: list[UserFairShareDTO] = Field(description="List of user fair shares")
    pagination: PaginationInfo = Field(description="Pagination information")


# Usage Bucket Common


class UsageBucketMetadataDTO(BaseModel):
    """Common metadata for usage bucket records."""

    period_start: date = Field(description="Start date of the usage measurement period (inclusive)")
    period_end: date = Field(description="End date of the usage measurement period (exclusive)")
    decay_unit_days: int = Field(description="Number of days in each decay unit for this bucket")
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")

    # BA-4202: Fair Share Metric calculation fields
    average_daily_usage: ResourceSlotDTO = Field(
        description="Average daily resource usage during this period"
    )
    usage_capacity_ratio: ResourceSlotDTO = Field(
        description="Ratio of usage to capacity (usage / total capacity available)"
    )
    average_capacity_per_second: ResourceSlotDTO = Field(
        description="Average capacity available per second during this period"
    )


# Domain Usage Bucket


class DomainUsageBucketDTO(BaseResponseModel):
    """
    Domain-level usage bucket representing aggregated resource consumption for a specific time period.

    Usage buckets store historical resource usage data that is used to calculate fair share factors.
    Each bucket represents usage during a decay unit period (typically one day).
    """

    id: UUID = Field(description="Unique identifier for this usage bucket record")
    domain_name: str = Field(description="Name of the domain this usage bucket belongs to")
    resource_group: str = Field(description="Name of the scaling group this usage was recorded in")
    metadata: UsageBucketMetadataDTO = Field(
        description="Metadata about the usage measurement period and timestamps"
    )
    resource_usage: ResourceSlotDTO = Field(
        description="Aggregated resource usage during this period (cpu, memory, accelerators)"
    )
    capacity_snapshot: ResourceSlotDTO = Field(
        description="Snapshot of total available capacity in the scaling group at the end of this period"
    )


class SearchDomainUsageBucketsResponse(BaseResponseModel):
    """Response for listing domain usage buckets."""

    items: list[DomainUsageBucketDTO] = Field(description="List of domain usage buckets")
    pagination: PaginationInfo = Field(description="Pagination information")


# Project Usage Bucket


class ProjectUsageBucketDTO(BaseResponseModel):
    """
    Project-level usage bucket representing aggregated resource consumption for a specific time period.

    Usage buckets store historical resource usage data that is used to calculate fair share factors.
    Each bucket represents usage during a decay unit period (typically one day).
    """

    id: UUID = Field(description="Unique identifier for this usage bucket record")
    project_id: UUID = Field(description="UUID of the project this usage bucket belongs to")
    domain_name: str = Field(description="Name of the domain the project belongs to")
    resource_group: str = Field(description="Name of the scaling group this usage was recorded in")
    metadata: UsageBucketMetadataDTO = Field(
        description="Metadata about the usage measurement period and timestamps"
    )
    resource_usage: ResourceSlotDTO = Field(
        description="Aggregated resource usage during this period (cpu, memory, accelerators)"
    )
    capacity_snapshot: ResourceSlotDTO = Field(
        description="Snapshot of total available capacity in the scaling group at the end of this period"
    )


class SearchProjectUsageBucketsResponse(BaseResponseModel):
    """Response for listing project usage buckets."""

    items: list[ProjectUsageBucketDTO] = Field(description="List of project usage buckets")
    pagination: PaginationInfo = Field(description="Pagination information")


# User Usage Bucket


class UserUsageBucketDTO(BaseResponseModel):
    """
    User-level usage bucket representing aggregated resource consumption for a specific time period.

    Usage buckets store historical resource usage data that is used to calculate fair share factors.
    Each bucket represents usage during a decay unit period (typically one day).
    This is the most granular level of usage tracking.
    """

    id: UUID = Field(description="Unique identifier for this usage bucket record")
    user_uuid: UUID = Field(description="UUID of the user this usage bucket belongs to")
    project_id: UUID = Field(description="UUID of the project the user belongs to")
    domain_name: str = Field(description="Name of the domain the user belongs to")
    resource_group: str = Field(description="Name of the scaling group this usage was recorded in")
    metadata: UsageBucketMetadataDTO = Field(
        description="Metadata about the usage measurement period and timestamps"
    )
    resource_usage: ResourceSlotDTO = Field(
        description="Aggregated resource usage during this period (cpu, memory, accelerators)"
    )
    capacity_snapshot: ResourceSlotDTO = Field(
        description="Snapshot of total available capacity in the scaling group at the end of this period"
    )


class SearchUserUsageBucketsResponse(BaseResponseModel):
    """Response for listing user usage buckets."""

    items: list[UserUsageBucketDTO] = Field(description="List of user usage buckets")
    pagination: PaginationInfo = Field(description="Pagination information")


# Upsert Weight Responses


class UpsertDomainFairShareWeightResponse(BaseResponseModel):
    """Response for upserting domain fair share weight."""

    item: DomainFairShareDTO = Field(description="Updated domain fair share data")


class UpsertProjectFairShareWeightResponse(BaseResponseModel):
    """Response for upserting project fair share weight."""

    item: ProjectFairShareDTO = Field(description="Updated project fair share data")


class UpsertUserFairShareWeightResponse(BaseResponseModel):
    """Response for upserting user fair share weight."""

    item: UserFairShareDTO = Field(description="Updated user fair share data")


# Bulk Upsert Weight Responses


class BulkUpsertDomainFairShareWeightResponse(BaseResponseModel):
    """Response for bulk upserting domain fair share weights."""

    upserted_count: int = Field(description="Number of records upserted")


class BulkUpsertProjectFairShareWeightResponse(BaseResponseModel):
    """Response for bulk upserting project fair share weights."""

    upserted_count: int = Field(description="Number of records upserted")


class BulkUpsertUserFairShareWeightResponse(BaseResponseModel):
    """Response for bulk upserting user fair share weights."""

    upserted_count: int = Field(description="Number of records upserted")


# Resource Group Fair Share Spec


class ResourceGroupFairShareSpecDTO(BaseModel):
    """Fair share specification for a resource group."""

    half_life_days: int = Field(description="Half-life for exponential decay in days")
    lookback_days: int = Field(description="Total lookback period in days")
    decay_unit_days: int = Field(description="Granularity of decay buckets in days")
    default_weight: Decimal = Field(description="Default weight for entities")
    resource_weights: ResourceSlotDTO = Field(description="Weights for each resource type")


class UpdateResourceGroupFairShareSpecResponse(BaseResponseModel):
    """Response for updating resource group fair share spec."""

    resource_group: str = Field(description="Name of the resource group")
    fair_share_spec: ResourceGroupFairShareSpecDTO = Field(
        description="Updated fair share specification"
    )


class GetResourceGroupFairShareSpecResponse(BaseResponseModel):
    """Response for getting resource group fair share spec."""

    resource_group: str = Field(description="Name of the resource group")
    fair_share_spec: ResourceGroupFairShareSpecDTO = Field(description="Fair share specification")


class ResourceGroupFairShareSpecItemDTO(BaseModel):
    """Resource group with its fair share specification."""

    resource_group: str = Field(description="Name of the resource group")
    fair_share_spec: ResourceGroupFairShareSpecDTO = Field(description="Fair share specification")


class SearchResourceGroupFairShareSpecsResponse(BaseResponseModel):
    """Response for searching resource group fair share specs."""

    items: list[ResourceGroupFairShareSpecItemDTO] = Field(
        description="List of resource group fair share specs"
    )
    total_count: int = Field(description="Total count of resource groups")
