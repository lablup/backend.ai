"""
Response DTOs for fair_share DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import (
    FairShareCalculationSnapshotInfo,
    FairShareSpecInfo,
    ResourceSlotInfo,
    UsageBucketMetadataInfo,
)

__all__ = (
    # Fair share nodes
    "DomainFairShareNode",
    "ProjectFairShareNode",
    "UserFairShareNode",
    # Usage bucket nodes
    "DomainUsageBucketNode",
    "ProjectUsageBucketNode",
    "UserUsageBucketNode",
    # Resource group spec node
    "ResourceGroupFairShareSpecNode",
    # Get payloads
    "GetDomainFairSharePayload",
    "GetProjectFairSharePayload",
    "GetUserFairSharePayload",
    # Search payloads
    "SearchDomainFairSharesPayload",
    "SearchProjectFairSharesPayload",
    "SearchUserFairSharesPayload",
    "SearchDomainUsageBucketsPayload",
    "SearchProjectUsageBucketsPayload",
    "SearchUserUsageBucketsPayload",
    # Upsert weight payloads
    "UpsertDomainFairShareWeightPayload",
    "UpsertProjectFairShareWeightPayload",
    "UpsertUserFairShareWeightPayload",
    # Bulk upsert weight payloads
    "BulkUpsertDomainFairShareWeightPayload",
    "BulkUpsertProjectFairShareWeightPayload",
    "BulkUpsertUserFairShareWeightPayload",
    # Resource group spec payloads
    "UpdateResourceGroupFairShareSpecPayload",
    "GetResourceGroupFairShareSpecPayload",
)


# Fair share nodes


class DomainFairShareNode(BaseResponseModel):
    """
    Domain-level fair share data representing scheduling priority for an entire domain.

    The fair share factor determines how resources are allocated to a domain relative to
    other domains within the same scaling group. A lower factor indicates higher priority.
    """

    id: str = Field(description="Unique identifier for this fair share record")
    resource_group_name: str = Field(
        description="Name of the scaling group this fair share belongs to"
    )
    domain_name: str = Field(description="Name of the domain this fair share is calculated for")
    spec: FairShareSpecInfo = Field(
        description="Fair share specification parameters used for calculation"
    )
    calculation_snapshot: FairShareCalculationSnapshotInfo = Field(
        description="Snapshot of the most recent fair share calculation results"
    )
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")


class ProjectFairShareNode(BaseResponseModel):
    """
    Project-level fair share data representing scheduling priority for a specific project.

    The fair share factor determines how resources are allocated to a project relative to
    other projects within the same domain and scaling group. A lower factor indicates
    higher priority.
    """

    id: str = Field(description="Unique identifier for this fair share record")
    resource_group_name: str = Field(
        description="Name of the scaling group this fair share belongs to"
    )
    project_id: UUID = Field(description="UUID of the project this fair share is calculated for")
    domain_name: str = Field(description="Name of the domain the project belongs to")
    spec: FairShareSpecInfo = Field(
        description="Fair share specification parameters used for calculation"
    )
    calculation_snapshot: FairShareCalculationSnapshotInfo = Field(
        description="Snapshot of the most recent fair share calculation results"
    )
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")


class UserFairShareNode(BaseResponseModel):
    """
    User-level fair share data representing scheduling priority for an individual user.

    The fair share factor determines how resources are allocated to a user relative to
    other users within the same project and scaling group. A lower factor indicates
    higher priority. This is the most granular level of fair share calculation.
    """

    id: str = Field(description="Unique identifier for this fair share record")
    resource_group_name: str = Field(
        description="Name of the scaling group this fair share belongs to"
    )
    user_uuid: UUID = Field(description="UUID of the user this fair share is calculated for")
    project_id: UUID = Field(description="UUID of the project the user belongs to")
    domain_name: str = Field(description="Name of the domain the user belongs to")
    spec: FairShareSpecInfo = Field(
        description="Fair share specification parameters used for calculation"
    )
    calculation_snapshot: FairShareCalculationSnapshotInfo = Field(
        description="Snapshot of the most recent fair share calculation results"
    )
    created_at: datetime = Field(description="Timestamp when this record was created")
    updated_at: datetime = Field(description="Timestamp when this record was last updated")


# Usage bucket nodes


class DomainUsageBucketNode(BaseResponseModel):
    """
    Domain-level usage bucket representing aggregated resource consumption for a time period.

    Usage buckets store historical resource usage data used to calculate fair share factors.
    Each bucket represents usage during a decay unit period (typically one day).
    """

    id: UUID = Field(description="Unique identifier for this usage bucket record")
    domain_name: str = Field(description="Name of the domain this usage bucket belongs to")
    resource_group: str = Field(description="Name of the scaling group this usage was recorded in")
    metadata: UsageBucketMetadataInfo = Field(
        description="Metadata about the usage measurement period and timestamps"
    )
    resource_usage: ResourceSlotInfo = Field(
        description="Aggregated resource usage during this period (cpu, memory, accelerators)"
    )
    capacity_snapshot: ResourceSlotInfo = Field(
        description=(
            "Snapshot of total available capacity in the scaling group at the end of this period"
        )
    )


class ProjectUsageBucketNode(BaseResponseModel):
    """
    Project-level usage bucket representing aggregated resource consumption for a time period.

    Usage buckets store historical resource usage data used to calculate fair share factors.
    Each bucket represents usage during a decay unit period (typically one day).
    """

    id: UUID = Field(description="Unique identifier for this usage bucket record")
    project_id: UUID = Field(description="UUID of the project this usage bucket belongs to")
    domain_name: str = Field(description="Name of the domain the project belongs to")
    resource_group: str = Field(description="Name of the scaling group this usage was recorded in")
    metadata: UsageBucketMetadataInfo = Field(
        description="Metadata about the usage measurement period and timestamps"
    )
    resource_usage: ResourceSlotInfo = Field(
        description="Aggregated resource usage during this period (cpu, memory, accelerators)"
    )
    capacity_snapshot: ResourceSlotInfo = Field(
        description=(
            "Snapshot of total available capacity in the scaling group at the end of this period"
        )
    )


class UserUsageBucketNode(BaseResponseModel):
    """
    User-level usage bucket representing aggregated resource consumption for a time period.

    Usage buckets store historical resource usage data used to calculate fair share factors.
    Each bucket represents usage during a decay unit period (typically one day).
    This is the most granular level of usage tracking.
    """

    id: UUID = Field(description="Unique identifier for this usage bucket record")
    user_uuid: UUID = Field(description="UUID of the user this usage bucket belongs to")
    project_id: UUID = Field(description="UUID of the project the user belongs to")
    domain_name: str = Field(description="Name of the domain the user belongs to")
    resource_group: str = Field(description="Name of the scaling group this usage was recorded in")
    metadata: UsageBucketMetadataInfo = Field(
        description="Metadata about the usage measurement period and timestamps"
    )
    resource_usage: ResourceSlotInfo = Field(
        description="Aggregated resource usage during this period (cpu, memory, accelerators)"
    )
    capacity_snapshot: ResourceSlotInfo = Field(
        description=(
            "Snapshot of total available capacity in the scaling group at the end of this period"
        )
    )


# Resource group spec node


class ResourceGroupFairShareSpecNode(BaseResponseModel):
    """Fair share specification for a resource group."""

    half_life_days: int = Field(description="Half-life for exponential decay in days")
    lookback_days: int = Field(description="Total lookback period in days")
    decay_unit_days: int = Field(description="Granularity of decay buckets in days")
    default_weight: Decimal = Field(description="Default weight for entities")
    resource_weights: ResourceSlotInfo = Field(description="Weights for each resource type")


# Get payloads


class GetDomainFairSharePayload(BaseResponseModel):
    """Payload for getting a single domain fair share."""

    item: DomainFairShareNode | None = Field(default=None, description="Domain fair share data")


class GetProjectFairSharePayload(BaseResponseModel):
    """Payload for getting a single project fair share."""

    item: ProjectFairShareNode | None = Field(default=None, description="Project fair share data")


class GetUserFairSharePayload(BaseResponseModel):
    """Payload for getting a single user fair share."""

    item: UserFairShareNode | None = Field(default=None, description="User fair share data")


# Search payloads


class SearchDomainFairSharesPayload(BaseResponseModel):
    """Payload for searching domain fair shares."""

    items: list[DomainFairShareNode] = Field(description="List of domain fair shares")
    total_count: int = Field(description="Total count of matching records")


class SearchProjectFairSharesPayload(BaseResponseModel):
    """Payload for searching project fair shares."""

    items: list[ProjectFairShareNode] = Field(description="List of project fair shares")
    total_count: int = Field(description="Total count of matching records")


class SearchUserFairSharesPayload(BaseResponseModel):
    """Payload for searching user fair shares."""

    items: list[UserFairShareNode] = Field(description="List of user fair shares")
    total_count: int = Field(description="Total count of matching records")


class SearchDomainUsageBucketsPayload(BaseResponseModel):
    """Payload for searching domain usage buckets."""

    items: list[DomainUsageBucketNode] = Field(description="List of domain usage buckets")
    total_count: int = Field(description="Total count of matching records")


class SearchProjectUsageBucketsPayload(BaseResponseModel):
    """Payload for searching project usage buckets."""

    items: list[ProjectUsageBucketNode] = Field(description="List of project usage buckets")
    total_count: int = Field(description="Total count of matching records")


class SearchUserUsageBucketsPayload(BaseResponseModel):
    """Payload for searching user usage buckets."""

    items: list[UserUsageBucketNode] = Field(description="List of user usage buckets")
    total_count: int = Field(description="Total count of matching records")


# Upsert weight payloads


class UpsertDomainFairShareWeightPayload(BaseResponseModel):
    """Payload for upserting domain fair share weight."""

    domain_fair_share: DomainFairShareNode = Field(description="Updated domain fair share data")


class UpsertProjectFairShareWeightPayload(BaseResponseModel):
    """Payload for upserting project fair share weight."""

    project_fair_share: ProjectFairShareNode = Field(description="Updated project fair share data")


class UpsertUserFairShareWeightPayload(BaseResponseModel):
    """Payload for upserting user fair share weight."""

    user_fair_share: UserFairShareNode = Field(description="Updated user fair share data")


# Bulk upsert weight payloads


class BulkUpsertDomainFairShareWeightPayload(BaseResponseModel):
    """Payload for bulk upserting domain fair share weights."""

    upserted_count: int = Field(description="Number of records upserted")


class BulkUpsertProjectFairShareWeightPayload(BaseResponseModel):
    """Payload for bulk upserting project fair share weights."""

    upserted_count: int = Field(description="Number of records upserted")


class BulkUpsertUserFairShareWeightPayload(BaseResponseModel):
    """Payload for bulk upserting user fair share weights."""

    upserted_count: int = Field(description="Number of records upserted")


# Resource group spec payloads


class UpdateResourceGroupFairShareSpecPayload(BaseResponseModel):
    """Payload for updating resource group fair share spec."""

    resource_group: str = Field(description="Name of the resource group")
    fair_share_spec: ResourceGroupFairShareSpecNode = Field(
        description="Updated fair share specification"
    )


class GetResourceGroupFairShareSpecPayload(BaseResponseModel):
    """Payload for getting resource group fair share spec."""

    resource_group: str = Field(description="Name of the resource group")
    fair_share_spec: ResourceGroupFairShareSpecNode = Field(description="Fair share specification")
