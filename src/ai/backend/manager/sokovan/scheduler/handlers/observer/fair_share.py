"""Fair share observer for tracking kernel resource usage.

This observer periodically records resource usage for kernels
to support fair share scheduling calculations.

Targets:
- Running kernels (terminated_at IS NULL)
- Recently terminated kernels with unobserved periods
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, override

from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.base import BulkCreator, QueryCondition
from ai.backend.manager.repositories.scheduler.options import KernelConditions
from ai.backend.manager.sokovan.scheduler.fair_share import FairShareAggregator

from .base import KernelObserver, ObservationResult

if TYPE_CHECKING:
    from ai.backend.manager.repositories.resource_usage_history import (
        ResourceUsageHistoryRepository,
    )
    from ai.backend.manager.repositories.scheduler import SchedulerRepository


class FairShareObserver(KernelObserver):
    """Observes kernels and updates fair share data.

    This observer performs three main operations:
    1. Records kernel resource usage (resource-seconds) via _record_kernel_usage()
    2. Aggregates usage into buckets via _aggregate_usage_buckets() (TODO)
    3. Calculates fair share ranks via _calculate_fair_share_ranks() (TODO)

    Targets:
    - Running kernels (terminated_at IS NULL, starts_at IS NOT NULL)
    - Recently terminated kernels with unobserved periods
      (terminated_at > last_observed_at, within lookback window)

    No kernel status transitions are performed.
    This is a pure observation operation for collecting usage data.
    """

    def __init__(
        self,
        aggregator: FairShareAggregator,
        resource_usage_repository: ResourceUsageHistoryRepository,
        scheduler_repository: SchedulerRepository,
    ) -> None:
        self._aggregator = aggregator
        self._resource_usage_repository = resource_usage_repository
        self._scheduler_repository = scheduler_repository

    @classmethod
    @override
    def name(cls) -> str:
        return "FairShareObserver"

    @override
    def get_query_condition(self, scaling_group: str) -> QueryCondition:
        """Get query condition for fair share observation.

        Returns a condition that matches:
        1. Running kernels (terminated_at IS NULL) with starts_at set
        2. Recently terminated kernels with unobserved periods

        The lookback_days is fetched from scaling_group's fair_share_spec via subquery.

        Args:
            scaling_group: The scaling group being processed

        Returns:
            QueryCondition for fair share observation targets
        """
        return KernelConditions.for_fair_share_observation(scaling_group)

    @override
    async def observe(
        self,
        scaling_group: str,
        kernels: Sequence[KernelInfo],
    ) -> ObservationResult:
        """Observe kernel usage and update fair share data.

        Args:
            scaling_group: The scaling group being processed
            kernels: Kernels to observe (running + recently terminated with unobserved periods)

        Returns:
            ObservationResult containing observed count
        """
        if not kernels:
            return ObservationResult(observed_count=0)

        now = await self._scheduler_repository.get_db_now()

        # Step 1: Record kernel usage (prepare + persist atomically)
        observed_count = await self._record_kernel_usage(scaling_group, kernels, now)

        # Step 2: Aggregate usage into buckets (TODO)
        # await self._aggregate_usage_buckets(scaling_group, now)

        # Step 3: Calculate fair share ranks (TODO)
        # await self._calculate_fair_share_ranks(scaling_group)

        return ObservationResult(observed_count=observed_count)

    async def _record_kernel_usage(
        self,
        scaling_group: str,
        kernels: Sequence[KernelInfo],
        now: datetime,
    ) -> int:
        """Record kernel resource usage and update observation timestamps.

        Prepares kernel usage records (pure computation via aggregator) and
        persists them atomically with last_observed_at updates.

        Args:
            scaling_group: The scaling group being processed
            kernels: Kernels to record usage for
            now: Current DB time for HA consistency

        Returns:
            Number of kernels with recorded usage
        """
        preparation_result = self._aggregator.prepare_kernel_usage_records(
            kernels, scaling_group, now
        )

        if not preparation_result.specs:
            return 0

        bulk_creator = BulkCreator(specs=preparation_result.specs)
        await self._resource_usage_repository.bulk_create_kernel_usage_records_with_observation_update(
            bulk_creator,
            preparation_result.kernel_observation_times,
        )

        return preparation_result.observed_count
