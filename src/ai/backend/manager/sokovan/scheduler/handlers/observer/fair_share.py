"""Fair share observer for tracking kernel resource usage.

This observer periodically records resource usage for kernels
to support fair share scheduling calculations.

Targets:
- Running kernels (terminated_at IS NULL)
- Recently terminated kernels with unobserved periods
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import date, timedelta
from typing import TYPE_CHECKING, override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.repositories.base import BulkCreator, QueryCondition
from ai.backend.manager.repositories.scheduler.options import KernelConditions
from ai.backend.manager.sokovan.scheduler.fair_share import (
    FairShareAggregator,
    FairShareFactorCalculator,
)

from .base import KernelObserver, ObservationResult

if TYPE_CHECKING:
    from ai.backend.manager.repositories.fair_share import FairShareRepository
    from ai.backend.manager.repositories.resource_usage_history import (
        ResourceUsageHistoryRepository,
    )
    from ai.backend.manager.repositories.scheduler import SchedulerRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class FairShareObserver(KernelObserver):
    """Observes kernels and updates fair share data.

    This observer performs operations in two main phases:

    Phase 1: Usage Recording
    - Prepare kernel usage records (pure computation)
    - Aggregate to daily buckets (pure computation)
    - Persist usage data to DB

    Phase 2: Factor and Rank Calculation
    - Read fair shares and decayed usages from DB (batched)
    - Calculate fair share factors (pure computation)
    - Calculate scheduling ranks from factors (pure computation)
    - Persist factors and ranks to DB (batched)

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
        calculator: FairShareFactorCalculator,
        resource_usage_repository: ResourceUsageHistoryRepository,
        fair_share_repository: FairShareRepository,
        scheduler_repository: SchedulerRepository,
    ) -> None:
        self._aggregator = aggregator
        self._calculator = calculator
        self._resource_usage_repository = resource_usage_repository
        self._fair_share_repository = fair_share_repository
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

        Operations are performed in two phases for efficient DB batching:

        Phase 1: Record usage
        - Prepare usage records (pure)
        - Aggregate to buckets (pure)
        - DB write: usage records + bucket increments

        Phase 2: Calculate and update factors + ranks
        - DB read: fair shares + decayed usages (batched)
        - Calculate factors (pure)
        - Calculate ranks from factors (pure, no DB read)
        - DB write: factors + ranks (batched)

        Args:
            scaling_group: The scaling group being processed
            kernels: Kernels to observe (running + recently terminated with unobserved periods)

        Returns:
            ObservationResult containing observed count
        """
        if not kernels:
            return ObservationResult(observed_count=0)

        now = await self._scheduler_repository.get_db_now()

        # ===== Phase 1: Record usage =====
        preparation_result = self._aggregator.prepare_kernel_usage_records(
            kernels, scaling_group, now
        )

        if not preparation_result.specs:
            return ObservationResult(observed_count=0)

        # Aggregate to daily buckets (pure computation)
        aggregation_result = self._aggregator.aggregate_kernel_usage_to_buckets(
            preparation_result.specs
        )

        # Atomic DB write for usage records
        bulk_creator = BulkCreator(specs=preparation_result.specs)
        await self._resource_usage_repository.record_fair_share_observation(
            bulk_creator,
            preparation_result.kernel_observation_times,
            aggregation_result,
        )

        # ===== Phase 2: Calculate and update factors + ranks =====
        await self._calculate_and_update_factors_and_ranks(scaling_group, now.date())

        return ObservationResult(observed_count=preparation_result.observed_count)

    async def _calculate_and_update_factors_and_ranks(
        self,
        scaling_group: str,
        today: date,
    ) -> None:
        """Calculate fair share factors and scheduling ranks, then update tables.

        This method batches DB operations:
        1. READ: scaling group config + fair shares + decayed usages (single session)
        2. PURE: calculate factors from usage with config
        3. PURE: calculate ranks from factors (no DB read needed)
        4. WRITE: update factors + ranks together

        Args:
            scaling_group: The scaling group being processed
            today: Current date for decay calculation
        """
        try:
            # ===== Single batched DB read =====
            # Get all data needed for calculation in one database session
            context = await self._fair_share_repository.get_fair_share_calculation_context(
                scaling_group, today
            )

            # Skip if no usage data
            if context.raw_usage_buckets.is_empty():
                return

            # ===== Pure computation: factors + ranks =====
            calculation_result = self._calculator.calculate_factors(context)

            # Skip if no results
            if not (
                calculation_result.domain_results
                or calculation_result.project_results
                or calculation_result.user_results
            ):
                return

            # Calculate lookback_start for DB write
            lookback_start = today - timedelta(days=context.lookback_days)

            # ===== Batched DB write: factors + ranks =====
            await self._fair_share_repository.bulk_update_fair_share_factors(
                scaling_group,
                calculation_result,
                lookback_start,
                today,
            )

        except Exception as e:
            log.warning(
                "Failed to calculate fair share factors and ranks for {}: {}",
                scaling_group,
                e,
            )
            # Don't fail the observation for calculation errors
