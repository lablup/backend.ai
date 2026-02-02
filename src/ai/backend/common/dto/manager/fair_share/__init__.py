"""Fair Share DTOs package."""

from __future__ import annotations

from .request import (
    GetDomainFairSharePathParam,
    GetDomainFairShareRequest,
    GetProjectFairSharePathParam,
    GetProjectFairShareRequest,
    GetResourceGroupFairShareSpecPathParam,
    GetUserFairSharePathParam,
    GetUserFairShareRequest,
    ResourceWeightEntryInput,
    RGDomainFairSharePathParam,
    RGDomainFairShareSearchPathParam,
    RGProjectFairSharePathParam,
    RGProjectFairShareSearchPathParam,
    RGUserFairSharePathParam,
    RGUserFairShareSearchPathParam,
    SearchDomainFairSharesRequest,
    SearchDomainUsageBucketsRequest,
    SearchProjectFairSharesRequest,
    SearchProjectUsageBucketsRequest,
    SearchUserFairSharesRequest,
    SearchUserUsageBucketsRequest,
    UpdateResourceGroupFairShareSpecPathParam,
    UpdateResourceGroupFairShareSpecRequest,
    UpsertDomainFairShareWeightPathParam,
    UpsertDomainFairShareWeightRequest,
    UpsertProjectFairShareWeightPathParam,
    UpsertProjectFairShareWeightRequest,
    UpsertUserFairShareWeightPathParam,
    UpsertUserFairShareWeightRequest,
)
from .response import (
    DomainFairShareDTO,
    DomainUsageBucketDTO,
    FairShareCalculationSnapshotDTO,
    FairShareSpecDTO,
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetResourceGroupFairShareSpecResponse,
    GetUserFairShareResponse,
    PaginationInfo,
    ProjectFairShareDTO,
    ProjectUsageBucketDTO,
    ResourceGroupFairShareSpecDTO,
    ResourceGroupFairShareSpecItemDTO,
    ResourceSlotDTO,
    ResourceSlotEntryDTO,
    SearchDomainFairSharesResponse,
    SearchDomainUsageBucketsResponse,
    SearchProjectFairSharesResponse,
    SearchProjectUsageBucketsResponse,
    SearchResourceGroupFairShareSpecsResponse,
    SearchUserFairSharesResponse,
    SearchUserUsageBucketsResponse,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightResponse,
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
    # Request - Path Parameters (Get)
    "GetDomainFairSharePathParam",
    "GetProjectFairSharePathParam",
    "GetUserFairSharePathParam",
    # Request - Path Parameters (Upsert Weight)
    "UpsertDomainFairShareWeightPathParam",
    "UpsertProjectFairShareWeightPathParam",
    "UpsertUserFairShareWeightPathParam",
    # Request - Path Parameters (Get Spec)
    "GetResourceGroupFairShareSpecPathParam",
    # Request - Path Parameters (Update Spec)
    "UpdateResourceGroupFairShareSpecPathParam",
    # Request - Path Parameters (RG Scoped)
    "RGDomainFairSharePathParam",
    "RGDomainFairShareSearchPathParam",
    "RGProjectFairSharePathParam",
    "RGProjectFairShareSearchPathParam",
    "RGUserFairSharePathParam",
    "RGUserFairShareSearchPathParam",
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
    # Request - Upsert Weight
    "UpsertDomainFairShareWeightRequest",
    "UpsertProjectFairShareWeightRequest",
    "UpsertUserFairShareWeightRequest",
    # Request - Update Spec
    "ResourceWeightEntryInput",
    "UpdateResourceGroupFairShareSpecRequest",
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
    "UpsertDomainFairShareWeightResponse",
    # Response - Project Fair Share
    "ProjectFairShareDTO",
    "GetProjectFairShareResponse",
    "SearchProjectFairSharesResponse",
    "UpsertProjectFairShareWeightResponse",
    # Response - User Fair Share
    "UserFairShareDTO",
    "GetUserFairShareResponse",
    "SearchUserFairSharesResponse",
    "UpsertUserFairShareWeightResponse",
    # Response - Domain Usage Bucket
    "DomainUsageBucketDTO",
    "SearchDomainUsageBucketsResponse",
    # Response - Project Usage Bucket
    "ProjectUsageBucketDTO",
    "SearchProjectUsageBucketsResponse",
    # Response - User Usage Bucket
    "UserUsageBucketDTO",
    "SearchUserUsageBucketsResponse",
    # Response - Resource Group Fair Share Spec
    "ResourceGroupFairShareSpecDTO",
    "ResourceGroupFairShareSpecItemDTO",
    "GetResourceGroupFairShareSpecResponse",
    "SearchResourceGroupFairShareSpecsResponse",
    "UpdateResourceGroupFairShareSpecResponse",
)
