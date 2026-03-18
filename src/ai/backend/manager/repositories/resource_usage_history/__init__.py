"""Resource Usage History repository package."""

from .creators import (
    DomainUsageBucketCreatorSpec,
    KernelUsageRecordCreatorSpec,
    ProjectUsageBucketCreatorSpec,
    UserUsageBucketCreatorSpec,
)
from .options import (
    DomainUsageBucketConditions,
    DomainUsageBucketOrders,
    KernelUsageRecordConditions,
    KernelUsageRecordOrders,
    ProjectUsageBucketConditions,
    ProjectUsageBucketOrders,
    UserUsageBucketConditions,
    UserUsageBucketOrders,
)
from .repositories import ResourceUsageHistoryRepositories
from .repository import ResourceUsageHistoryRepository
from .types import (
    DomainUsageBucketData,
    DomainUsageBucketSearchResult,
    DomainUsageBucketSearchScope,
    KernelUsageRecordData,
    KernelUsageRecordSearchResult,
    ProjectUsageBucketData,
    ProjectUsageBucketSearchResult,
    ProjectUsageBucketSearchScope,
    UserUsageBucketData,
    UserUsageBucketSearchResult,
    UserUsageBucketSearchScope,
)
from .upserters import (
    DomainUsageBucketUpserterSpec,
    ProjectUsageBucketUpserterSpec,
    UserUsageBucketUpserterSpec,
)

__all__ = (
    # Repositories
    "ResourceUsageHistoryRepositories",
    "ResourceUsageHistoryRepository",
    # Data types
    "KernelUsageRecordData",
    "DomainUsageBucketData",
    "ProjectUsageBucketData",
    "UserUsageBucketData",
    # Search result types
    "KernelUsageRecordSearchResult",
    "DomainUsageBucketSearchResult",
    "ProjectUsageBucketSearchResult",
    "UserUsageBucketSearchResult",
    # Search scope types
    "DomainUsageBucketSearchScope",
    "ProjectUsageBucketSearchScope",
    "UserUsageBucketSearchScope",
    # Creator specs
    "KernelUsageRecordCreatorSpec",
    "DomainUsageBucketCreatorSpec",
    "ProjectUsageBucketCreatorSpec",
    "UserUsageBucketCreatorSpec",
    # Upserter specs
    "DomainUsageBucketUpserterSpec",
    "ProjectUsageBucketUpserterSpec",
    "UserUsageBucketUpserterSpec",
    # Query conditions
    "KernelUsageRecordConditions",
    "DomainUsageBucketConditions",
    "ProjectUsageBucketConditions",
    "UserUsageBucketConditions",
    # Query orders
    "KernelUsageRecordOrders",
    "DomainUsageBucketOrders",
    "ProjectUsageBucketOrders",
    "UserUsageBucketOrders",
)
