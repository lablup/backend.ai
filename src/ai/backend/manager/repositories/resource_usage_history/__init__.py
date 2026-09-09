"""Resource Usage History repository package."""

from ai.backend.manager.data.resource_usage_history.types import (
    DomainUsageBucketData,
    KernelUsageRecordData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    DomainUsageBucketSearchResult,
    KernelUsageRecordSearchResult,
    ProjectUsageBucketSearchResult,
    UserUsageBucketSearchResult,
)

from .creators import KernelUsageRecordCreatorSpec
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
    # Creator specs
    "KernelUsageRecordCreatorSpec",
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
