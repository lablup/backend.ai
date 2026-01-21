"""Fair share factor calculator.

This module calculates fair share factors for domain/project/user
based on aggregated usage from usage buckets with time decay applied.

The fair share factor formula is:
    F = 2^(-normalized_usage / weight)

Where:
- F ranges from 0.0 to 1.0 (higher = higher priority)
- normalized_usage is the weighted sum of resource usage
- weight is the priority multiplier (higher weight = less penalty for same usage)
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from ai.backend.common.types import ResourceSlot

if TYPE_CHECKING:
    from ai.backend.manager.data.fair_share.types import (
        DomainFairShareData,
        ProjectFairShareData,
        UserFairShareData,
    )


# Default resource weights for fair share calculation
DEFAULT_RESOURCE_WEIGHTS: ResourceSlot = ResourceSlot({
    "cpu": Decimal("1.0"),
    "mem": Decimal("0.001"),  # Memory is in bytes, so lower weight
    "cuda.device": Decimal("10.0"),  # GPU is typically more valuable
    "cuda.shares": Decimal("10.0"),
})

# Normalizing constant to scale usage_score to reasonable range
# This affects the steepness of the decay curve
# Higher value = gentler decay (less difference between high and low usage)
DEFAULT_USAGE_SCALE = Decimal("86400")  # 1 day in seconds


@dataclass(frozen=True)
class DecayedUsageResult:
    """Result of aggregating usage with time decay."""

    total_decayed_usage: ResourceSlot
    lookback_start: date
    lookback_end: date


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


@dataclass
class FairShareFactorCalculationResult:
    """Result of fair share factor calculation for all levels."""

    domain_results: dict[str, DomainFactorResult] = field(default_factory=dict)
    project_results: dict[UUID, ProjectFactorResult] = field(default_factory=dict)
    user_results: dict[tuple[UUID, UUID], UserFactorResult] = field(default_factory=dict)


class FairShareFactorCalculator:
    """Calculates fair share factors from aggregated usage.

    This calculator performs pure computation without database interactions.
    It takes aggregated usage data and existing fair share configurations,
    then computes updated factor values.
    """

    def __init__(
        self,
        resource_weights: ResourceSlot | None = None,
        usage_scale: Decimal | None = None,
    ) -> None:
        """Initialize the calculator.

        Args:
            resource_weights: Weights for each resource type in factor calculation.
                             If None, uses DEFAULT_RESOURCE_WEIGHTS.
            usage_scale: Normalizing constant for usage score.
                        If None, uses DEFAULT_USAGE_SCALE.
        """
        self._resource_weights = resource_weights or DEFAULT_RESOURCE_WEIGHTS
        self._usage_scale = usage_scale or DEFAULT_USAGE_SCALE

    def calculate_factors(
        self,
        domain_usages: Mapping[str, ResourceSlot],
        project_usages: Mapping[UUID, ResourceSlot],
        user_usages: Mapping[tuple[UUID, UUID], ResourceSlot],
        domain_fair_shares: Mapping[str, DomainFairShareData],
        project_fair_shares: Mapping[UUID, ProjectFairShareData],
        user_fair_shares: Mapping[tuple[UUID, UUID], UserFairShareData],
        lookback_start: date,
        lookback_end: date,
    ) -> FairShareFactorCalculationResult:
        """Calculate fair share factors for all levels.

        Args:
            domain_usages: Aggregated decayed usage by domain_name
            project_usages: Aggregated decayed usage by project_id
            user_usages: Aggregated decayed usage by (user_uuid, project_id)
            domain_fair_shares: Current domain fair share data (for weight)
            project_fair_shares: Current project fair share data (for weight)
            user_fair_shares: Current user fair share data (for weight)
            lookback_start: Start of lookback period
            lookback_end: End of lookback period

        Returns:
            FairShareFactorCalculationResult with computed factors
        """
        result = FairShareFactorCalculationResult()

        # Calculate domain factors
        for domain_name, usage in domain_usages.items():
            weight = Decimal("1.0")
            if domain_name in domain_fair_shares:
                weight = domain_fair_shares[domain_name].spec.weight

            factor_result = self._calculate_factor(
                usage=usage,
                weight=weight,
                resource_weights=self._get_resource_weights(domain_fair_shares.get(domain_name)),
            )

            result.domain_results[domain_name] = DomainFactorResult(
                domain_name=domain_name,
                total_decayed_usage=usage,
                normalized_usage=factor_result[0],
                fair_share_factor=factor_result[1],
            )

        # Calculate project factors
        for project_id, usage in project_usages.items():
            weight = Decimal("1.0")
            domain_name = ""
            if project_id in project_fair_shares:
                weight = project_fair_shares[project_id].spec.weight
                domain_name = project_fair_shares[project_id].domain_name

            factor_result = self._calculate_factor(
                usage=usage,
                weight=weight,
                resource_weights=self._get_resource_weights(project_fair_shares.get(project_id)),
            )

            result.project_results[project_id] = ProjectFactorResult(
                project_id=project_id,
                domain_name=domain_name,
                total_decayed_usage=usage,
                normalized_usage=factor_result[0],
                fair_share_factor=factor_result[1],
            )

        # Calculate user factors
        for (user_uuid, project_id), usage in user_usages.items():
            weight = Decimal("1.0")
            domain_name = ""
            if (user_uuid, project_id) in user_fair_shares:
                weight = user_fair_shares[(user_uuid, project_id)].spec.weight
                domain_name = user_fair_shares[(user_uuid, project_id)].domain_name

            factor_result = self._calculate_factor(
                usage=usage,
                weight=weight,
                resource_weights=self._get_resource_weights(
                    user_fair_shares.get((user_uuid, project_id))
                ),
            )

            result.user_results[(user_uuid, project_id)] = UserFactorResult(
                user_uuid=user_uuid,
                project_id=project_id,
                domain_name=domain_name,
                total_decayed_usage=usage,
                normalized_usage=factor_result[0],
                fair_share_factor=factor_result[1],
            )

        return result

    def _get_resource_weights(
        self,
        fair_share_data: DomainFairShareData | ProjectFairShareData | UserFairShareData | None,
    ) -> ResourceSlot:
        """Get resource weights from fair share data or use defaults."""
        if fair_share_data is not None:
            spec_weights = fair_share_data.spec.resource_weights
            if spec_weights and len(spec_weights) > 0:
                return spec_weights
        return self._resource_weights

    def _calculate_factor(
        self,
        usage: ResourceSlot,
        weight: Decimal,
        resource_weights: ResourceSlot,
    ) -> tuple[Decimal, Decimal]:
        """Calculate normalized_usage and fair_share_factor.

        Args:
            usage: Total decayed resource usage (resource-seconds)
            weight: Priority weight multiplier
            resource_weights: Weights for each resource type

        Returns:
            Tuple of (normalized_usage, fair_share_factor)
        """
        # Calculate weighted usage score
        usage_score = self._calculate_usage_score(usage, resource_weights)

        # Normalize by scale factor
        normalized_usage = usage_score / self._usage_scale

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


def apply_time_decay(
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


def aggregate_with_decay(
    buckets: Mapping[date, ResourceSlot],
    today: date,
    half_life_days: int,
    lookback_days: int,
) -> DecayedUsageResult:
    """Aggregate usage buckets with time decay.

    Args:
        buckets: Usage by bucket date
        today: Current date
        half_life_days: Number of days for usage to decay to 50%
        lookback_days: Number of days to look back

    Returns:
        DecayedUsageResult with total decayed usage
    """
    from datetime import timedelta

    lookback_start = today - timedelta(days=lookback_days)
    total_decayed = ResourceSlot()

    for bucket_date, usage in buckets.items():
        if bucket_date < lookback_start:
            continue
        if bucket_date > today:
            continue

        decayed = apply_time_decay(usage, bucket_date, today, half_life_days)
        total_decayed = total_decayed + decayed

    return DecayedUsageResult(
        total_decayed_usage=total_decayed,
        lookback_start=lookback_start,
        lookback_end=today,
    )
