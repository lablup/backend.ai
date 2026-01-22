"""Fair share factor calculator.

This module calculates fair share factors for domain/project/user
based on aggregated usage from usage buckets with time decay applied.

The fair share factor formula is:
    F = 2^(-normalized_usage / weight)

Where:
- F ranges from 0.0 to 1.0 (higher = higher priority)
- normalized_usage is the weighted sum of resource usage
- weight is the priority multiplier (higher weight = less penalty for same usage)

The decay formula is:
    decayed_usage = usage * 2^(-(days_ago) / half_life_days)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.types import ResourceSlot

if TYPE_CHECKING:
    from ai.backend.manager.data.fair_share.types import (
        DomainFairShareData,
        FairShareCalculationContext,
        ProjectFairShareData,
        RawUsageBucketsByLevel,
        UserFairShareData,
    )

from ai.backend.manager.data.fair_share import UserProjectKey

# Default resource weights for fair share calculation
DEFAULT_RESOURCE_WEIGHTS: ResourceSlot = ResourceSlot({
    "cpu": Decimal("1.0"),
    "mem": Decimal("0.001"),  # Memory is in bytes, so lower weight
    "cuda.device": Decimal("10.0"),  # GPU is typically more valuable
    "cuda.shares": Decimal("10.0"),
})

# Seconds per day for time capacity calculation
SECONDS_PER_DAY = Decimal("86400")


@dataclass(frozen=True)
class DomainFactorResult:
    """Factor calculation result for a domain."""

    domain_name: str
    total_decayed_usage: ResourceSlot
    normalized_usage: Decimal
    fair_share_factor: Decimal


@dataclass(frozen=True)
class ProjectFactorResult:
    """Factor calculation result for a project."""

    project_id: UUID
    domain_name: str
    total_decayed_usage: ResourceSlot
    normalized_usage: Decimal
    fair_share_factor: Decimal


@dataclass(frozen=True)
class UserFactorResult:
    """Factor calculation result for a user."""

    user_uuid: UUID
    project_id: UUID
    domain_name: str
    total_decayed_usage: ResourceSlot
    normalized_usage: Decimal
    fair_share_factor: Decimal


@dataclass(frozen=True)
class UserSchedulingRank:
    """Scheduling rank for a user within a project."""

    user_uuid: UUID
    project_id: UUID
    rank: int  # 1 = highest priority


@dataclass(frozen=True)
class _UserFactorForRanking:
    """Internal dataclass for sorting users by hierarchical factors."""

    user_uuid: UUID
    project_id: UUID
    domain_factor: Decimal
    project_factor: Decimal
    user_factor: Decimal

    def sort_key(self) -> tuple[Decimal, Decimal, Decimal]:
        """Return sort key for descending order (higher factor = higher priority)."""
        return (-self.domain_factor, -self.project_factor, -self.user_factor)


@dataclass
class FairShareFactorCalculationResult:
    """Result of fair share factor calculation for all levels."""

    domain_results: dict[str, DomainFactorResult] = field(default_factory=dict)
    project_results: dict[UUID, ProjectFactorResult] = field(default_factory=dict)
    user_results: dict[UserProjectKey, UserFactorResult] = field(default_factory=dict)
    scheduling_ranks: list[UserSchedulingRank] = field(default_factory=list)


class FairShareFactorCalculator:
    """Calculates fair share factors from aggregated usage.

    This calculator performs pure computation without database interactions.
    It takes aggregated usage data and existing fair share configurations,
    then computes updated factor values.
    """

    def __init__(
        self,
        resource_weights: ResourceSlot | None = None,
    ) -> None:
        """Initialize the calculator.

        Args:
            resource_weights: Weights for each resource type in factor calculation.
                             If None, uses DEFAULT_RESOURCE_WEIGHTS.
        """
        self._resource_weights = resource_weights or DEFAULT_RESOURCE_WEIGHTS

    def calculate_factors(
        self,
        context: FairShareCalculationContext,
    ) -> FairShareFactorCalculationResult:
        """Calculate fair share factors for all levels.

        This method:
        1. Applies time decay to raw usage buckets
        2. Aggregates decayed usage per entity
        3. Calculates fair share factors
        4. Computes scheduling ranks

        Args:
            context: Calculation context containing fair shares, raw usage buckets,
                    and configuration (default_weight, resource_weights, half_life_days, today)

        Returns:
            FairShareFactorCalculationResult with computed factors and scheduling ranks
        """
        result = FairShareFactorCalculationResult()

        fair_shares = context.fair_shares
        default_weight = context.default_weight
        default_resource_weights = context.resource_weights or self._resource_weights

        # Apply time decay to raw buckets and aggregate
        decayed_usages = self._aggregate_with_decay(
            context.raw_usage_buckets,
            context.today,
            context.half_life_days,
        )

        # Calculate time capacity based on half-life
        # This normalizes usage relative to the decay window
        time_capacity = Decimal(str(context.half_life_days)) * SECONDS_PER_DAY

        # Calculate domain factors
        for domain_name, usage in decayed_usages["domain"].items():
            weight = default_weight
            if domain_name in fair_shares.domain:
                weight = fair_shares.domain[domain_name].spec.weight

            factor_result = self._calculate_factor(
                usage=usage,
                weight=weight,
                resource_weights=self._get_resource_weights(
                    fair_shares.domain.get(domain_name), default_resource_weights
                ),
                time_capacity=time_capacity,
            )

            result.domain_results[domain_name] = DomainFactorResult(
                domain_name=domain_name,
                total_decayed_usage=usage,
                normalized_usage=factor_result[0],
                fair_share_factor=factor_result[1],
            )

        # Calculate project factors
        for project_id, usage in decayed_usages["project"].items():
            weight = default_weight
            domain_name = ""
            if project_id in fair_shares.project:
                weight = fair_shares.project[project_id].spec.weight
                domain_name = fair_shares.project[project_id].domain_name

            factor_result = self._calculate_factor(
                usage=usage,
                weight=weight,
                resource_weights=self._get_resource_weights(
                    fair_shares.project.get(project_id), default_resource_weights
                ),
                time_capacity=time_capacity,
            )

            result.project_results[project_id] = ProjectFactorResult(
                project_id=project_id,
                domain_name=domain_name,
                total_decayed_usage=usage,
                normalized_usage=factor_result[0],
                fair_share_factor=factor_result[1],
            )

        # Calculate user factors
        for user_key, usage in decayed_usages["user"].items():
            weight = default_weight
            domain_name = ""
            if user_key in fair_shares.user:
                weight = fair_shares.user[user_key].spec.weight
                domain_name = fair_shares.user[user_key].domain_name

            factor_result = self._calculate_factor(
                usage=usage,
                weight=weight,
                resource_weights=self._get_resource_weights(
                    fair_shares.user.get(user_key), default_resource_weights
                ),
                time_capacity=time_capacity,
            )

            result.user_results[user_key] = UserFactorResult(
                user_uuid=user_key.user_uuid,
                project_id=user_key.project_id,
                domain_name=domain_name,
                total_decayed_usage=usage,
                normalized_usage=factor_result[0],
                fair_share_factor=factor_result[1],
            )

        # Calculate scheduling ranks from factors
        result.scheduling_ranks = self._calculate_scheduling_ranks(result)

        return result

    def _aggregate_with_decay(
        self,
        raw_buckets: RawUsageBucketsByLevel,
        today: date,
        half_life_days: int,
    ) -> dict[str, dict]:
        """Aggregate raw usage buckets with time decay applied.

        Args:
            raw_buckets: Raw usage buckets per entity per date
            today: Current date for decay calculation
            half_life_days: Number of days for usage to decay to 50%

        Returns:
            Dictionary with decayed and aggregated usage by level:
            - "domain": Mapping[str, ResourceSlot]
            - "project": Mapping[UUID, ResourceSlot]
            - "user": Mapping[UserProjectKey, ResourceSlot]
        """
        # Aggregate domain usage with decay
        domain_decayed: dict[str, ResourceSlot] = {}
        for domain_name, date_buckets in raw_buckets.domain.items():
            total = ResourceSlot()
            for bucket_date, usage in date_buckets.items():
                decayed = self._apply_time_decay(usage, bucket_date, today, half_life_days)
                total = total + decayed
            domain_decayed[domain_name] = total

        # Aggregate project usage with decay
        project_decayed: dict[UUID, ResourceSlot] = {}
        for project_id, date_buckets in raw_buckets.project.items():
            total = ResourceSlot()
            for bucket_date, usage in date_buckets.items():
                decayed = self._apply_time_decay(usage, bucket_date, today, half_life_days)
                total = total + decayed
            project_decayed[project_id] = total

        # Aggregate user usage with decay
        user_decayed: dict[UserProjectKey, ResourceSlot] = {}
        for user_key, date_buckets in raw_buckets.user.items():
            total = ResourceSlot()
            for bucket_date, usage in date_buckets.items():
                decayed = self._apply_time_decay(usage, bucket_date, today, half_life_days)
                total = total + decayed
            user_decayed[user_key] = total

        return {
            "domain": domain_decayed,
            "project": project_decayed,
            "user": user_decayed,
        }

    def _apply_time_decay(
        self,
        usage: ResourceSlot,
        bucket_date: date,
        today: date,
        half_life_days: int,
    ) -> ResourceSlot:
        """Apply exponential time decay to resource usage.

        Formula: decayed_usage = usage * 2^(-(days_ago) / half_life_days)

        Args:
            usage: Raw resource usage
            bucket_date: Date of the usage bucket
            today: Current date
            half_life_days: Number of days for usage to decay to 50%

        Returns:
            Decayed resource usage
        """
        days_ago = (today - bucket_date).days
        if days_ago < 0:
            # Future bucket (shouldn't happen, but handle gracefully)
            return usage

        if days_ago == 0:
            # No decay for today's usage
            return usage

        # Calculate decay factor: 2^(-days_ago / half_life_days)
        exponent = Decimal(str(-days_ago)) / Decimal(str(half_life_days))
        decay_factor = Decimal("2") ** exponent

        # Apply decay to all resources
        return ResourceSlot({key: value * decay_factor for key, value in usage.items()})

    def _get_resource_weights(
        self,
        fair_share_data: DomainFairShareData | ProjectFairShareData | UserFairShareData | None,
        default_weights: ResourceSlot,
    ) -> ResourceSlot:
        """Get resource weights from fair share data or use defaults.

        Args:
            fair_share_data: Fair share data containing per-entity resource weights
            default_weights: Default weights from scaling group config

        Returns:
            ResourceSlot with weights for each resource type
        """
        if fair_share_data is not None:
            spec_weights = fair_share_data.spec.resource_weights
            if spec_weights and len(spec_weights) > 0:
                return spec_weights
        return default_weights

    def _calculate_factor(
        self,
        usage: ResourceSlot,
        weight: Decimal,
        resource_weights: ResourceSlot,
        time_capacity: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """Calculate normalized_usage and fair_share_factor.

        Args:
            usage: Total decayed resource usage (resource-seconds)
            weight: Priority weight multiplier
            resource_weights: Weights for each resource type
            time_capacity: Time-based normalization factor (half_life_days * SECONDS_PER_DAY)

        Returns:
            Tuple of (normalized_usage, fair_share_factor)
        """
        # Calculate weighted usage score
        usage_score = self._calculate_usage_score(usage, resource_weights)

        # Normalize by time capacity (derived from half-life)
        normalized_usage = usage_score / time_capacity

        # Calculate fair share factor: F = 2^(-normalized_usage / weight)
        # Clamp to prevent overflow/underflow
        exponent = -normalized_usage / weight
        exponent = max(min(exponent, Decimal("10")), Decimal("-10"))

        # Use Python's power for Decimal
        fair_share_factor = Decimal("2") ** exponent

        # Clamp factor to [0, 1] range
        fair_share_factor = max(min(fair_share_factor, Decimal("1.0")), Decimal("0.0"))

        return normalized_usage, fair_share_factor

    def _calculate_usage_score(
        self,
        usage: ResourceSlot,
        resource_weights: ResourceSlot,
    ) -> Decimal:
        """Calculate weighted sum of resource usage.

        Args:
            usage: Resource usage (resource-seconds)
            resource_weights: Weights for each resource type

        Returns:
            Weighted usage score
        """
        total_score = Decimal("0")
        total_weight = Decimal("0")

        for resource_key, resource_value in usage.items():
            weight = resource_weights.get(resource_key, Decimal("1.0"))
            total_score += resource_value * weight
            total_weight += weight

        # Normalize by total weight to get weighted average
        if total_weight > 0:
            return total_score / total_weight

        return Decimal("0")

    def _calculate_scheduling_ranks(
        self,
        calculation_result: FairShareFactorCalculationResult,
    ) -> list[UserSchedulingRank]:
        """Calculate scheduling ranks from factor calculation results.

        Sorts users by hierarchical fair share factors (domain, project, user)
        and assigns ranks. Lower rank = higher priority (1 = highest).

        Sorting order: domain_factor DESC, project_factor DESC, user_factor DESC

        Args:
            calculation_result: Result from calculate_factors()

        Returns:
            List of UserSchedulingRank with assigned ranks
        """
        if not calculation_result.user_results:
            return []

        # Build list of user factors for ranking
        user_factors: list[_UserFactorForRanking] = []

        for user_key, user_result in calculation_result.user_results.items():
            # Get domain factor (default to 1.0 if not found)
            domain_factor = Decimal("1.0")
            if user_result.domain_name in calculation_result.domain_results:
                domain_factor = calculation_result.domain_results[
                    user_result.domain_name
                ].fair_share_factor

            # Get project factor (default to 1.0 if not found)
            project_factor = Decimal("1.0")
            if user_key.project_id in calculation_result.project_results:
                project_factor = calculation_result.project_results[
                    user_key.project_id
                ].fair_share_factor

            user_factors.append(
                _UserFactorForRanking(
                    user_uuid=user_key.user_uuid,
                    project_id=user_key.project_id,
                    domain_factor=domain_factor,
                    project_factor=project_factor,
                    user_factor=user_result.fair_share_factor,
                )
            )

        # Sort by factors descending (higher factor = higher priority = lower rank)
        sorted_factors = sorted(user_factors, key=lambda f: f.sort_key())

        # Assign ranks (1 = highest priority)
        return [
            UserSchedulingRank(
                user_uuid=factor.user_uuid,
                project_id=factor.project_id,
                rank=rank,
            )
            for rank, factor in enumerate(sorted_factors, start=1)
        ]
