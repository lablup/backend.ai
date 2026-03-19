"""
Request DTOs for fair_share DTO v2.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateRangeFilter, StringFilter, UUIDFilter

from .types import (
    DomainFairShareOrderField,
    DomainUsageBucketOrderField,
    OrderDirection,
    ProjectFairShareOrderField,
    ProjectUsageBucketOrderField,
    UserFairShareOrderField,
    UserUsageBucketOrderField,
)

__all__ = (
    # Filter models
    "DomainFairShareFilter",
    "ProjectFairShareFilter",
    "UserFairShareFilter",
    "DomainUsageBucketFilter",
    "ProjectUsageBucketFilter",
    "UserUsageBucketFilter",
    # Order models
    "DomainFairShareOrder",
    "ProjectFairShareOrder",
    "UserFairShareOrder",
    "DomainUsageBucketOrder",
    "ProjectUsageBucketOrder",
    "UserUsageBucketOrder",
    # Get inputs
    "GetDomainFairShareInput",
    "GetProjectFairShareInput",
    "GetUserFairShareInput",
    "GetResourceGroupFairShareSpecInput",
    # Search inputs
    "SearchDomainFairSharesInput",
    "SearchProjectFairSharesInput",
    "SearchUserFairSharesInput",
    "SearchDomainUsageBucketsInput",
    "SearchProjectUsageBucketsInput",
    "SearchUserUsageBucketsInput",
    # Upsert weight inputs
    "UpsertDomainFairShareWeightInput",
    "UpsertProjectFairShareWeightInput",
    "UpsertUserFairShareWeightInput",
    # Bulk upsert entry types
    "DomainWeightEntryInput",
    "ProjectWeightEntryInput",
    "UserWeightEntryInput",
    # Bulk upsert inputs
    "BulkUpsertDomainFairShareWeightInput",
    "BulkUpsertProjectFairShareWeightInput",
    "BulkUpsertUserFairShareWeightInput",
    # Update spec
    "ResourceWeightEntryInput",
    "UpdateResourceGroupFairShareSpecInput",
)

_DEFAULT_PAGE_LIMIT = 50


# Filter models


class DomainFairShareFilter(BaseRequestModel):
    """Filter for domain fair share queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class ProjectFairShareFilter(BaseRequestModel):
    """Filter for project fair share queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class UserFairShareFilter(BaseRequestModel):
    """Filter for user fair share queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    user_uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")


class DomainUsageBucketFilter(BaseRequestModel):
    """Filter for domain usage bucket queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    period_start: DateRangeFilter | None = Field(
        default=None, description="Filter by period start date"
    )


class ProjectUsageBucketFilter(BaseRequestModel):
    """Filter for project usage bucket queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    period_start: DateRangeFilter | None = Field(
        default=None, description="Filter by period start date"
    )


class UserUsageBucketFilter(BaseRequestModel):
    """Filter for user usage bucket queries."""

    resource_group: StringFilter | None = Field(default=None, description="Filter by scaling group")
    user_uuid: UUIDFilter | None = Field(default=None, description="Filter by user UUID")
    project_id: UUIDFilter | None = Field(default=None, description="Filter by project ID")
    domain_name: StringFilter | None = Field(default=None, description="Filter by domain name")
    period_start: DateRangeFilter | None = Field(
        default=None, description="Filter by period start date"
    )


# Order models


class DomainFairShareOrder(BaseRequestModel):
    """Order specification for domain fair share queries."""

    field: DomainFairShareOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class ProjectFairShareOrder(BaseRequestModel):
    """Order specification for project fair share queries."""

    field: ProjectFairShareOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class UserFairShareOrder(BaseRequestModel):
    """Order specification for user fair share queries."""

    field: UserFairShareOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class DomainUsageBucketOrder(BaseRequestModel):
    """Order specification for domain usage bucket queries."""

    field: DomainUsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class ProjectUsageBucketOrder(BaseRequestModel):
    """Order specification for project usage bucket queries."""

    field: ProjectUsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


class UserUsageBucketOrder(BaseRequestModel):
    """Order specification for user usage bucket queries."""

    field: UserUsageBucketOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.DESC, description="Order direction")


# Get inputs (path parameters mapped to Input models)


class GetDomainFairShareInput(BaseRequestModel):
    """Input for getting a single domain fair share."""

    resource_group: str = Field(description="Scaling group name")
    domain_name: str = Field(description="Domain name")


class GetProjectFairShareInput(BaseRequestModel):
    """Input for getting a single project fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")


class GetUserFairShareInput(BaseRequestModel):
    """Input for getting a single user fair share."""

    resource_group: str = Field(description="Scaling group name")
    project_id: UUID = Field(description="Project ID")
    user_uuid: UUID = Field(description="User UUID")


class GetResourceGroupFairShareSpecInput(BaseRequestModel):
    """Input for getting resource group fair share spec."""

    resource_group: str = Field(description="Scaling group name")


# Search inputs


class SearchDomainFairSharesInput(BaseRequestModel):
    """Input for searching domain fair shares."""

    filter: DomainFairShareFilter | None = Field(default=None, description="Filter conditions")
    order: list[DomainFairShareOrder] | None = Field(
        default=None, description="Order specifications"
    )
    first: int | None = Field(default=None, ge=1, description="Cursor-based: items after cursor")
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(default=None, ge=1, description="Cursor-based: items before cursor")
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Offset-based: max results")
    offset: int | None = Field(default=None, ge=0, description="Offset-based: pagination offset")


class SearchProjectFairSharesInput(BaseRequestModel):
    """Input for searching project fair shares."""

    filter: ProjectFairShareFilter | None = Field(default=None, description="Filter conditions")
    order: list[ProjectFairShareOrder] | None = Field(
        default=None, description="Order specifications"
    )
    first: int | None = Field(default=None, ge=1, description="Cursor-based: items after cursor")
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(default=None, ge=1, description="Cursor-based: items before cursor")
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Offset-based: max results")
    offset: int | None = Field(default=None, ge=0, description="Offset-based: pagination offset")


class SearchUserFairSharesInput(BaseRequestModel):
    """Input for searching user fair shares."""

    filter: UserFairShareFilter | None = Field(default=None, description="Filter conditions")
    order: list[UserFairShareOrder] | None = Field(default=None, description="Order specifications")
    first: int | None = Field(default=None, ge=1, description="Cursor-based: items after cursor")
    after: str | None = Field(default=None, description="Cursor-based: start cursor (exclusive)")
    last: int | None = Field(default=None, ge=1, description="Cursor-based: items before cursor")
    before: str | None = Field(default=None, description="Cursor-based: end cursor (exclusive)")
    limit: int | None = Field(default=None, ge=1, le=1000, description="Offset-based: max results")
    offset: int | None = Field(default=None, ge=0, description="Offset-based: pagination offset")


class SearchDomainUsageBucketsInput(BaseRequestModel):
    """Input for searching domain usage buckets."""

    filter: DomainUsageBucketFilter | None = Field(default=None, description="Filter conditions")
    order: list[DomainUsageBucketOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=_DEFAULT_PAGE_LIMIT, ge=1, le=1000, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchProjectUsageBucketsInput(BaseRequestModel):
    """Input for searching project usage buckets."""

    filter: ProjectUsageBucketFilter | None = Field(default=None, description="Filter conditions")
    order: list[ProjectUsageBucketOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=_DEFAULT_PAGE_LIMIT, ge=1, le=1000, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class SearchUserUsageBucketsInput(BaseRequestModel):
    """Input for searching user usage buckets."""

    filter: UserUsageBucketFilter | None = Field(default=None, description="Filter conditions")
    order: list[UserUsageBucketOrder] | None = Field(
        default=None, description="Order specifications"
    )
    limit: int = Field(
        default=_DEFAULT_PAGE_LIMIT, ge=1, le=1000, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


# Upsert weight inputs


class UpsertDomainFairShareWeightInput(BaseRequestModel):
    """Input for upserting domain fair share weight."""

    resource_group_name: str = Field(description="Scaling group name.")
    domain_name: str = Field(description="Name of the domain to update weight for.")
    weight: Decimal | None = Field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority. "
            "Set to null to use resource group's default_weight."
        ),
    )


class UpsertProjectFairShareWeightInput(BaseRequestModel):
    """Input for upserting project fair share weight."""

    resource_group_name: str = Field(description="Scaling group name.")
    project_id: UUID = Field(description="UUID of the project to update weight for.")
    domain_name: str = Field(description="Name of the domain the project belongs to.")
    weight: Decimal | None = Field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority. "
            "Set to null to use resource group's default_weight."
        ),
    )


class UpsertUserFairShareWeightInput(BaseRequestModel):
    """Input for upserting user fair share weight."""

    resource_group_name: str = Field(description="Scaling group name.")
    user_uuid: UUID = Field(description="User UUID.")
    project_id: UUID = Field(description="Project ID.")
    domain_name: str = Field(description="Name of the domain the user belongs to.")
    weight: Decimal | None = Field(
        default=None,
        description=(
            "Priority weight multiplier. Higher weight = higher priority. "
            "Set to null to use resource group's default_weight."
        ),
    )


# Bulk upsert entry types


class DomainWeightEntryInput(BaseRequestModel):
    """Single domain weight entry for bulk upsert."""

    domain_name: str = Field(description="Domain name")
    weight: Decimal | None = Field(description="Fair share weight (null for default)")


class BulkUpsertDomainFairShareWeightInput(BaseRequestModel):
    """Input for bulk upserting domain fair share weights."""

    resource_group_name: str = Field(description="Scaling group name.")
    inputs: list[DomainWeightEntryInput] = Field(description="List of domain weights to upsert.")


class ProjectWeightEntryInput(BaseRequestModel):
    """Single project weight entry for bulk upsert."""

    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name for context")
    weight: Decimal | None = Field(description="Fair share weight (null for default)")


class BulkUpsertProjectFairShareWeightInput(BaseRequestModel):
    """Input for bulk upserting project fair share weights."""

    resource_group_name: str = Field(description="Scaling group name.")
    inputs: list[ProjectWeightEntryInput] = Field(description="List of project weights to upsert.")


class UserWeightEntryInput(BaseRequestModel):
    """Single user weight entry for bulk upsert."""

    user_uuid: UUID = Field(description="User UUID")
    project_id: UUID = Field(description="Project ID")
    domain_name: str = Field(description="Domain name for context")
    weight: Decimal | None = Field(description="Fair share weight (null for default)")


class BulkUpsertUserFairShareWeightInput(BaseRequestModel):
    """Input for bulk upserting user fair share weights."""

    resource_group_name: str = Field(description="Scaling group name.")
    inputs: list[UserWeightEntryInput] = Field(description="List of user weights to upsert.")


# Update spec input


class ResourceWeightEntryInput(BaseRequestModel):
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


class UpdateResourceGroupFairShareSpecInput(BaseRequestModel):
    """Input for updating resource group fair share spec (partial update).

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
