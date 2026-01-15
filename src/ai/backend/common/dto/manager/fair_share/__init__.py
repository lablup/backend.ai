"""Fair Share DTOs package."""

from __future__ import annotations

from .request import (
    GetDomainFairSharePathParam,
    GetDomainFairShareRequest,
    GetProjectFairSharePathParam,
    GetProjectFairShareRequest,
    GetUserFairSharePathParam,
    GetUserFairShareRequest,
    SearchDomainFairSharesRequest,
    SearchDomainUsageBucketsRequest,
    SearchProjectFairSharesRequest,
    SearchProjectUsageBucketsRequest,
    SearchUserFairSharesRequest,
    SearchUserUsageBucketsRequest,
)
from .response import (
    DomainFairShareDTO,
    DomainUsageBucketDTO,
    FairShareCalculationSnapshotDTO,
    FairShareSpecDTO,
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetUserFairShareResponse,
    PaginationInfo,
    ProjectFairShareDTO,
    ProjectUsageBucketDTO,
    ResourceSlotDTO,
    ResourceSlotEntryDTO,
    SearchDomainFairSharesResponse,
    SearchDomainUsageBucketsResponse,
    SearchProjectFairSharesResponse,
    SearchProjectUsageBucketsResponse,
    SearchUserFairSharesResponse,
    SearchUserUsageBucketsResponse,
    UsageBucketMetadataDTO,
    UserFairShareDTO,
    UserUsageBucketDTO,
)
from .types import (
    DomainFairShareFilter,
    DomainFairShareOrder,
    DomainFairShareOrderField,
    DomainUsageBucketFilter,
    DomainUsageBucketOrder,
    DomainUsageBucketOrderField,
    OrderDirection,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    ProjectFairShareOrderField,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrder,
    ProjectUsageBucketOrderField,
    UserFairShareFilter,
    UserFairShareOrder,
    UserFairShareOrderField,
    UserUsageBucketFilter,
    UserUsageBucketOrder,
    UserUsageBucketOrderField,
)

__all__ = (
    # Types - Enums
    "OrderDirection",
    # Types - Domain Fair Share
    "DomainFairShareOrderField",
    "DomainFairShareFilter",
    "DomainFairShareOrder",
    # Types - Project Fair Share
    "ProjectFairShareOrderField",
    "ProjectFairShareFilter",
    "ProjectFairShareOrder",
    # Types - User Fair Share
    "UserFairShareOrderField",
    "UserFairShareFilter",
    "UserFairShareOrder",
    # Types - Domain Usage Bucket
    "DomainUsageBucketOrderField",
    "DomainUsageBucketFilter",
    "DomainUsageBucketOrder",
    # Types - Project Usage Bucket
    "ProjectUsageBucketOrderField",
    "ProjectUsageBucketFilter",
    "ProjectUsageBucketOrder",
    # Types - User Usage Bucket
    "UserUsageBucketOrderField",
    "UserUsageBucketFilter",
    "UserUsageBucketOrder",
    # Request - Path Parameters
    "GetDomainFairSharePathParam",
    "GetProjectFairSharePathParam",
    "GetUserFairSharePathParam",
    # Request - Get (deprecated, use PathParam)
    "GetDomainFairShareRequest",
    "GetProjectFairShareRequest",
    "GetUserFairShareRequest",
    # Request - Search
    "SearchDomainFairSharesRequest",
    "SearchProjectFairSharesRequest",
    "SearchUserFairSharesRequest",
    "SearchDomainUsageBucketsRequest",
    "SearchProjectUsageBucketsRequest",
    "SearchUserUsageBucketsRequest",
    # Response - Common
    "PaginationInfo",
    "ResourceSlotEntryDTO",
    "ResourceSlotDTO",
    "FairShareSpecDTO",
    "FairShareCalculationSnapshotDTO",
    "UsageBucketMetadataDTO",
    # Response - Domain Fair Share
    "DomainFairShareDTO",
    "GetDomainFairShareResponse",
    "SearchDomainFairSharesResponse",
    # Response - Project Fair Share
    "ProjectFairShareDTO",
    "GetProjectFairShareResponse",
    "SearchProjectFairSharesResponse",
    # Response - User Fair Share
    "UserFairShareDTO",
    "GetUserFairShareResponse",
    "SearchUserFairSharesResponse",
    # Response - Domain Usage Bucket
    "DomainUsageBucketDTO",
    "SearchDomainUsageBucketsResponse",
    # Response - Project Usage Bucket
    "ProjectUsageBucketDTO",
    "SearchProjectUsageBucketsResponse",
    # Response - User Usage Bucket
    "UserUsageBucketDTO",
    "SearchUserUsageBucketsResponse",
)
