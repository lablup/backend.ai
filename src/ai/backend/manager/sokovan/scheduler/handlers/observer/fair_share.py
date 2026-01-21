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

# Default fair share configuration
DEFAULT_HALF_LIFE_DAYS = 7
DEFAULT_LOOKBACK_DAYS = 28


class FairShareObserver(KernelObserver):
    """Observes kernels and updates fair share data.

    This observer performs four main operations:
    1. Records kernel resource usage (resource-seconds)
    2. Updates last_observed_at for observed kernels
    3. Aggregates usage into daily buckets (user/project/domain)
    4. Calculates and updates fair share factors

    All DB writes are performed in transactions to ensure data consistency.

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

        All operations are performed in phases:
        1. Pure computation: prepare usage records and aggregate to buckets
        2. Atomic DB write: persist usage data
        3. Calculate fair share factors from aggregated usage
        4. Update fair share tables with new factors

        Args:
            scaling_group: The scaling group being processed
            kernels: Kernels to observe (running + recently terminated with unobserved periods)

        Returns:
            ObservationResult containing observed count
        """
        # ===== Phase 1: Record usage (even if no kernels, still calculate factors) =====
        observed_count = 0
        now = await self._scheduler_repository.get_db_now()

        if kernels:
            # Prepare kernel usage records
            preparation_result = self._aggregator.prepare_kernel_usage_records(
                kernels, scaling_group, now
            )

            if preparation_result.specs:
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
                observed_count = preparation_result.observed_count

        # ===== Phase 2: Calculate and update fair share factors =====
        await self._calculate_and_update_factors(scaling_group, now.date())

        return ObservationResult(observed_count=observed_count)

    async def _calculate_and_update_factors(
        self,
        scaling_group: str,
        today: date,
    ) -> None:
        """Calculate fair share factors and update tables.

        Args:
            scaling_group: The scaling group being processed
            today: Current date for decay calculation
        """
        # Get fair share configuration (use defaults for now)
        # TODO: Get from scaling group configuration
        half_life_days = DEFAULT_HALF_LIFE_DAYS
        lookback_days = DEFAULT_LOOKBACK_DAYS

        try:
            # Get current fair share records for weights
            (
                domain_fair_shares,
                project_fair_shares,
                user_fair_shares,
            ) = await self._fair_share_repository.get_all_fair_shares_for_resource_group(
                scaling_group
            )

            # Get aggregated usage with decay
            domain_usages = await self._resource_usage_repository.get_decayed_usage_by_domain(
                scaling_group, today, half_life_days, lookback_days
            )
            project_usages = await self._resource_usage_repository.get_decayed_usage_by_project(
                scaling_group, today, half_life_days, lookback_days
            )
            user_usages = await self._resource_usage_repository.get_decayed_usage_by_user(
                scaling_group, today, half_life_days, lookback_days
            )

            # Skip if no usage data
            if not domain_usages and not project_usages and not user_usages:
                return

            # Calculate factors
            lookback_start = today - timedelta(days=lookback_days)
            calculation_result = self._calculator.calculate_factors(
                domain_usages=domain_usages,
                project_usages=project_usages,
                user_usages=user_usages,
                domain_fair_shares=domain_fair_shares,
                project_fair_shares=project_fair_shares,
                user_fair_shares=user_fair_shares,
                lookback_start=lookback_start,
                lookback_end=today,
            )

            # Update fair share tables
            if (
                calculation_result.domain_results
                or calculation_result.project_results
                or calculation_result.user_results
            ):
                await self._fair_share_repository.bulk_update_fair_share_factors(
                    scaling_group,
                    calculation_result,
                    lookback_start,
                    today,
                )

        except Exception as e:
            log.warning(
                "Failed to calculate fair share factors for {}: {}",
                scaling_group,
                e,
            )
            # Don't fail the observation for factor calculation errors
