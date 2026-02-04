"""Request DTOs for Fair Share API."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseRequestModel

from .types import (
    DomainFairShareFilter,
    DomainFairShareOrder,
    DomainUsageBucketFilter,
    DomainUsageBucketOrder,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrder,
    UserFairShareFilter,
    UserFairShareOrder,
    UserUsageBucketFilter,
    UserUsageBucketOrder,
)

__all__ = (
    # Path parameters - Get
    "GetDomainFairSharePathParam",
    "GetProjectFairSharePathParam",
    "GetUserFairSharePathParam",
    # Path parameters - RG Scoped Get
    "RGDomainFairSharePathParam",
    "RGProjectFairSharePathParam",
    "RGUserFairSharePathParam",
    # Path parameters - RG Scoped Search
    "RGDomainFairShareSearchPathParam",
    "RGProjectFairShareSearchPathParam",
    "RGUserFairShareSearchPathParam",
    # Path parameters - Upsert Weight
    "UpsertDomainFairShareWeightPathParam",
    "UpsertProjectFairShareWeightPathParam",
    "UpsertUserFairShareWeightPathParam",
    # Path parameters - Update Spec
    "UpdateResourceGroupFairShareSpecPathParam",
    # Get requests (deprecated, use PathParam)
    "GetDomainFairShareRequest",
    "GetProjectFairShareRequest",
    "GetUserFairShareRequest",
    # Search requests
    "SearchDomainFairSharesRequest",
    "SearchProjectFairSharesRequest",
    "SearchUserFairSharesRequest",
    "SearchDomainUsageBucketsRequest",
    "SearchProjectUsageBucketsRequest",
    "SearchUserUsageBucketsRequest",
    # Upsert Weight Requests
    "UpsertDomainFairShareWeightRequest",
    "UpsertProjectFairShareWeightRequest",
    "UpsertUserFairShareWeightRequest",
    # Bulk Upsert Weight Requests
    "DomainWeightEntryInput",
    "BulkUpsertDomainFairShareWeightRequest",
    "ProjectWeightEntryInput",
    "BulkUpsertProjectFairShareWeightRequest",
    "UserWeightEntryInput",
    "BulkUpsertUserFairShareWeightRequest",
    # Update Spec Requests
    "ResourceWeightEntryInput",
    "UpdateResourceGroupFairShareSpecRequest",
)


# Path Parameters


class GetDomainFairSharePathParam(BaseRequestModel):
    """Path parameters for getting a single domain fair share."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class GetProjectFairSharePathParam(BaseRequestModel):
    """Path parameters for getting a single project fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")


class GetUserFairSharePathParam(BaseRequestModel):
    """Path parameters for getting a single user fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


# RG-Scoped Path Parameters


class RGDomainFairSharePathParam(BaseRequestModel):
    """Path parameters for RG-scoped domain fair share get."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class RGProjectFairSharePathParam(BaseRequestModel):
    """Path parameters for RG-scoped project fair share get."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")
    project_id: UUID = Field(description="Project ID")


class RGUserFairSharePathParam(BaseRequestModel):
    """Path parameters for RG-scoped user fair share get."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


class RGDomainFairShareSearchPathParam(BaseRequestModel):
    """Path parameters for RG-scoped domain fair share search."""

    resource_group: str = Field(description="Scaling group name")


class RGProjectFairShareSearchPathParam(BaseRequestModel):
    """Path parameters for RG-scoped project fair share search."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class RGUserFairShareSearchPathParam(BaseRequestModel):
    """Path parameters for RG-scoped user fair share search."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")
    project_id: UUID = Field(description="Project ID")


# Get Requests (deprecated, use PathParam models above)


class GetDomainFairShareRequest(BaseRequestModel):
    """Request for getting a single domain fair share."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class GetProjectFairShareRequest(BaseRequestModel):
    """Request for getting a single project fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")


class GetUserFairShareRequest(BaseRequestModel):
    """Request for getting a single user fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


# Search Requests


class SearchDomainFairSharesRequest(BaseRequestModel):
    """Request body for searching domain fair shares."""

    filter: DomainFairShareFilter | None = Field(default=None, description="Filter conditions")
    order: list[DomainFairShareOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchProjectFairSharesRequest(BaseRequestModel):
    """Request body for searching project fair shares."""

    filter: ProjectFairShareFilter | None = Field(default=None, description="Filter conditions")
    order: list[ProjectFairShareOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchUserFairSharesRequest(BaseRequestModel):
    """Request body for searching user fair shares."""

    filter: UserFairShareFilter | None = Field(default=None, description="Filter conditions")
    order: list[UserFairShareOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchDomainUsageBucketsRequest(BaseRequestModel):
    """Request body for searching domain usage buckets."""

    filter: DomainUsageBucketFilter | None = Field(default=None, description="Filter conditions")
    order: list[DomainUsageBucketOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchProjectUsageBucketsRequest(BaseRequestModel):
    """Request body for searching project usage buckets."""

    filter: ProjectUsageBucketFilter | None = Field(default=None, description="Filter conditions")
    order: list[ProjectUsageBucketOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchUserUsageBucketsRequest(BaseRequestModel):
    """Request body for searching user usage buckets."""

    filter: UserUsageBucketFilter | None = Field(default=None, description="Filter conditions")
    order: list[UserUsageBucketOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


# Upsert Weight Path Parameters


class UpsertDomainFairShareWeightPathParam(BaseRequestModel):
    """Path parameters for upserting domain fair share weight."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class UpsertProjectFairShareWeightPathParam(BaseRequestModel):
    """Path parameters for upserting project fair share weight."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")


class UpsertUserFairShareWeightPathParam(BaseRequestModel):
    """Path parameters for upserting user fair share weight."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


class UpdateResourceGroupFairShareSpecPathParam(BaseRequestModel):
    """Path parameters for updating resource group fair share spec."""

    resource_group: str = Field(description="Scaling group name")


class GetResourceGroupFairShareSpecPathParam(BaseRequestModel):
    """Path parameters for getting resource group fair share spec."""

    resource_group: str = Field(description="Scaling group name")


# Upsert Weight Request Bodies


class UpsertDomainFairShareWeightRequest(BaseRequestModel):
    """Request body for upserting domain fair share weight.

    Set weight to null to use the resource group's default_weight.
    """

    weight: Decimal | None = Field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority. "
            "Set to null to use resource group's default_weight."
        ),
    )


class UpsertProjectFairShareWeightRequest(BaseRequestModel):
    """Request body for upserting project fair share weight.

    Set weight to null to use the resource group's default_weight.
    """

    domain_name: str = Field(description="Domain name the project belongs to")
    weight: Decimal | None = Field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority. "
            "Set to null to use resource group's default_weight."
        ),
    )


class UpsertUserFairShareWeightRequest(BaseRequestModel):
    """Request body for upserting user fair share weight.

    Set weight to null to use the resource group's default_weight.
    """

    domain_name: str = Field(description="Domain name the user belongs to")
    weight: Decimal | None = Field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority. "
            "Set to null to use resource group's default_weight."
        ),
    )


# Update Resource Group Fair Share Spec


class ResourceWeightEntryInput(BaseModel):
    """A single resource weight entry for fair share calculation.

    Set weight to null to remove the resource type weight (revert to default).
    """

    resource_type: str = Field(description="Resource type identifier (e.g., cpu, mem, cuda.shares)")
    weight: Decimal | None = Field(
        default=None,
        description=(
            "Weight multiplier for this resource type. "
            "Set to null to remove (revert to default weight)."
        ),
    )


class UpdateResourceGroupFairShareSpecRequest(BaseRequestModel):
    """Request body for updating resource group fair share spec (partial update).

    All fields are optional. Only provided fields are updated; others retain existing values.
    """

    half_life_days: int | None = Field(
        default=None,
        description="Half-life for exponential decay in days. Leave null to keep existing value.",
    )
    lookback_days: int | None = Field(
        default=None,
        description="Total lookback period in days. Leave null to keep existing value.",
    )
    decay_unit_days: int | None = Field(
        default=None,
        description="Granularity of decay buckets in days. Leave null to keep existing value.",
    )
    default_weight: Decimal | None = Field(
        default=None,
        description="Default weight for entities. Leave null to keep existing value.",
    )
    resource_weights: list[ResourceWeightEntryInput] | None = Field(
        default=None,
        description=(
            "Resource weights for fair share calculation. "
            "Each entry specifies a resource type and its weight multiplier. "
            "Only provided resource types are updated (partial update). "
            "Set weight to null to remove that resource type (revert to default). "
            "Leave the entire list null to keep all existing values."
        ),
    )


# Bulk Upsert Weight Input Types


class DomainWeightEntryInput(BaseRequestModel):
    """Single domain weight entry for bulk upsert."""

    domain_name: str = Field(description="Domain name")
    weight: Decimal | None = Field(description="Fair share weight (null for default)")


class BulkUpsertDomainFairShareWeightRequest(BaseRequestModel):
    """Request to bulk upsert domain fair share weights."""

    resource_group: str = Field(description="Scaling group name")
    inputs: list[DomainWeightEntryInput] = Field(description="List of domain weights to upsert")


class ProjectWeightEntryInput(BaseRequestModel):
    """Single project weight entry for bulk upsert."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name for context")
    weight: Decimal | None = Field(description="Fair share weight (null for default)")


class BulkUpsertProjectFairShareWeightRequest(BaseRequestModel):
    """Request to bulk upsert project fair share weights."""

    resource_group: str = Field(description="Scaling group name")
    inputs: list[ProjectWeightEntryInput] = Field(description="List of project weights to upsert")


class UserWeightEntryInput(BaseRequestModel):
    """Single user weight entry for bulk upsert."""

    user_uuid: UUID = Field(description="User UUID")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name for context")
    weight: Decimal | None = Field(description="Fair share weight (null for default)")


class BulkUpsertUserFairShareWeightRequest(BaseRequestModel):
    """Request to bulk upsert user fair share weights."""

    resource_group: str = Field(description="Scaling group name")
    inputs: list[UserWeightEntryInput] = Field(description="List of user weights to upsert")
