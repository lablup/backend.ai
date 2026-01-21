"""Resource Usage History Repository with Resilience policies."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING

from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.resilience.policies.retry import BackoffStrategy
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.repositories.base import BatchQuerier, BulkCreator, Creator, Upserter

from .db_source import ResourceUsageHistoryDBSource
from .types import (
    DomainUsageBucketData,
    DomainUsageBucketSearchResult,
    KernelUsageRecordData,
    KernelUsageRecordSearchResult,
    ProjectUsageBucketData,
    ProjectUsageBucketSearchResult,
    UserUsageBucketData,
    UserUsageBucketSearchResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.resource_usage_history import (
        DomainUsageBucketRow,
        KernelUsageRecordRow,
        ProjectUsageBucketRow,
        UserUsageBucketRow,
    )
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


__all__ = ("ResourceUsageHistoryRepository",)


resource_usage_history_repository_resilience = Resilience(
    policies=[
        MetricPolicy(
            MetricArgs(
                domain=DomainType.REPOSITORY, layer=LayerType.RESOURCE_USAGE_HISTORY_REPOSITORY
            )
        ),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
            )
        ),
    ]
)


class ResourceUsageHistoryRepository:
    """Repository for Resource Usage History data access with resilience policies."""

    _db_source: ResourceUsageHistoryDBSource

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db_source = ResourceUsageHistoryDBSource(db)

    # ==================== Kernel Usage Records ====================

    @resource_usage_history_repository_resilience.apply()
    async def create_kernel_usage_record(
        self,
        creator: Creator[KernelUsageRecordRow],
    ) -> KernelUsageRecordData:
        """Create a single kernel usage record."""
        return await self._db_source.create_kernel_usage_record(creator)

    @resource_usage_history_repository_resilience.apply()
    async def bulk_create_kernel_usage_records(
        self,
        bulk_creator: BulkCreator[KernelUsageRecordRow],
    ) -> list[KernelUsageRecordData]:
        """Bulk create kernel usage records.

        This is the primary method used by UsageAggregationService to record
        per-period usage slices for all running kernels.
        """
        return await self._db_source.bulk_create_kernel_usage_records(bulk_creator)

    @resource_usage_history_repository_resilience.apply()
    async def bulk_create_kernel_usage_records_with_observation_update(
        self,
        bulk_creator: BulkCreator[KernelUsageRecordRow],
        kernel_observation_times: Mapping[uuid.UUID, datetime],
    ) -> tuple[list[KernelUsageRecordData], int]:
        """Bulk create kernel usage records and update observation timestamps atomically.

        This method performs both operations in a single transaction for data consistency:
        1. Bulk create kernel usage records
        2. Update last_observed_at for the observed kernels

        Used by FairShareObserver to record usage and update observation state atomically.

        Args:
            bulk_creator: Specs for creating kernel usage records
            kernel_observation_times: Mapping of kernel ID to observation timestamp

        Returns:
            Tuple of (created records data, number of kernels with updated observation times)
        """
        return await self._db_source.bulk_create_kernel_usage_records_with_observation_update(
            bulk_creator, kernel_observation_times
        )

    @resource_usage_history_repository_resilience.apply()
    async def search_kernel_usage_records(
        self,
        querier: BatchQuerier,
    ) -> KernelUsageRecordSearchResult:
        """Search kernel usage records with pagination."""
        return await self._db_source.search_kernel_usage_records(querier)

    # ==================== Domain Usage Buckets ====================

    @resource_usage_history_repository_resilience.apply()
    async def create_domain_usage_bucket(
        self,
        creator: Creator[DomainUsageBucketRow],
    ) -> DomainUsageBucketData:
        """Create a new domain usage bucket."""
        return await self._db_source.create_domain_usage_bucket(creator)

    @resource_usage_history_repository_resilience.apply()
    async def upsert_domain_usage_bucket(
        self,
        upserter: Upserter[DomainUsageBucketRow],
    ) -> DomainUsageBucketData:
        """Upsert a domain usage bucket."""
        return await self._db_source.upsert_domain_usage_bucket(upserter)

    @resource_usage_history_repository_resilience.apply()
    async def search_domain_usage_buckets(
        self,
        querier: BatchQuerier,
    ) -> DomainUsageBucketSearchResult:
        """Search domain usage buckets with pagination."""
        return await self._db_source.search_domain_usage_buckets(querier)

    # ==================== Project Usage Buckets ====================

    @resource_usage_history_repository_resilience.apply()
    async def create_project_usage_bucket(
        self,
        creator: Creator[ProjectUsageBucketRow],
    ) -> ProjectUsageBucketData:
        """Create a new project usage bucket."""
        return await self._db_source.create_project_usage_bucket(creator)

    @resource_usage_history_repository_resilience.apply()
    async def upsert_project_usage_bucket(
        self,
        upserter: Upserter[ProjectUsageBucketRow],
    ) -> ProjectUsageBucketData:
        """Upsert a project usage bucket."""
        return await self._db_source.upsert_project_usage_bucket(upserter)

    @resource_usage_history_repository_resilience.apply()
    async def search_project_usage_buckets(
        self,
        querier: BatchQuerier,
    ) -> ProjectUsageBucketSearchResult:
        """Search project usage buckets with pagination."""
        return await self._db_source.search_project_usage_buckets(querier)

    # ==================== User Usage Buckets ====================

    @resource_usage_history_repository_resilience.apply()
    async def create_user_usage_bucket(
        self,
        creator: Creator[UserUsageBucketRow],
    ) -> UserUsageBucketData:
        """Create a new user usage bucket."""
        return await self._db_source.create_user_usage_bucket(creator)

    @resource_usage_history_repository_resilience.apply()
    async def upsert_user_usage_bucket(
        self,
        upserter: Upserter[UserUsageBucketRow],
    ) -> UserUsageBucketData:
        """Upsert a user usage bucket."""
        return await self._db_source.upsert_user_usage_bucket(upserter)

    @resource_usage_history_repository_resilience.apply()
    async def search_user_usage_buckets(
        self,
        querier: BatchQuerier,
    ) -> UserUsageBucketSearchResult:
        """Search user usage buckets with pagination."""
        return await self._db_source.search_user_usage_buckets(querier)

    # ==================== Aggregation Queries ====================

    @resource_usage_history_repository_resilience.apply()
    async def get_aggregated_usage_by_user(
        self,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[tuple[uuid.UUID, uuid.UUID], ResourceSlot]:
        """Get aggregated usage by (user_uuid, project_id) pairs.

        This method aggregates resource_usage across all buckets within the
        lookback period for each user-project pair. Used by Fair Share
        calculation service.
        """
        return await self._db_source.get_aggregated_usage_by_user(
            resource_group, lookback_start, lookback_end
        )

    @resource_usage_history_repository_resilience.apply()
    async def get_aggregated_usage_by_project(
        self,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[uuid.UUID, ResourceSlot]:
        """Get aggregated usage by project_id.

        This method aggregates resource_usage across all buckets within the
        lookback period for each project.
        """
        return await self._db_source.get_aggregated_usage_by_project(
            resource_group, lookback_start, lookback_end
        )

    @resource_usage_history_repository_resilience.apply()
    async def get_aggregated_usage_by_domain(
        self,
        resource_group: str,
        lookback_start: date,
        lookback_end: date,
    ) -> Mapping[str, ResourceSlot]:
        """Get aggregated usage by domain_name.

        This method aggregates resource_usage across all buckets within the
        lookback period for each domain.
        """
        return await self._db_source.get_aggregated_usage_by_domain(
            resource_group, lookback_start, lookback_end
        )
