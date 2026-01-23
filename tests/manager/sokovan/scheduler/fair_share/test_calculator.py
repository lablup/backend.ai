"""Tests for FairShareFactorCalculator.

Verifies fair share factor calculation including:
- Time decay application (internal to calculator)
- Resource weight handling
- Factor calculation formula: F = 2^(-normalized_usage / weight)
- Scheduling rank assignment
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    FairShareCalculationContext,
    FairShareCalculationSnapshot,
    FairShareMetadata,
    FairSharesByLevel,
    FairShareSpec,
    ProjectFairShareData,
    RawUsageBucketsByLevel,
    UserFairShareData,
    UserProjectKey,
)
from ai.backend.manager.sokovan.scheduler.fair_share.calculator import (
    FairShareFactorCalculator,
)


def make_fair_share_spec(
    weight: Decimal = Decimal("1.0"),
    half_life_days: int = 7,
    lookback_days: int = 30,
) -> FairShareSpec:
    """Create a FairShareSpec for testing."""
    return FairShareSpec(
        weight=weight,
        half_life_days=half_life_days,
        lookback_days=lookback_days,
        decay_unit_days=1,
        resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.001")}),
    )


def make_calculation_snapshot() -> FairShareCalculationSnapshot:
    """Create a dummy calculation snapshot for testing."""
    from datetime import UTC, datetime

    return FairShareCalculationSnapshot(
        fair_share_factor=Decimal("1.0"),
        total_decayed_usage=ResourceSlot(),
        normalized_usage=Decimal("0"),
        lookback_start=date(2024, 1, 1),
        lookback_end=date(2024, 1, 15),
        last_calculated_at=datetime.now(UTC),
    )


def make_metadata() -> FairShareMetadata:
    """Create dummy metadata for testing."""
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return FairShareMetadata(created_at=now, updated_at=now)


@pytest.fixture
def calculator() -> FairShareFactorCalculator:
    """Create FairShareFactorCalculator with default resource weights."""
    return FairShareFactorCalculator(
        resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.001")})
    )


@pytest.fixture
def today() -> date:
    """Standard test date."""
    return date(2024, 1, 15)


class TestApplyTimeDecay:
    """Tests for _apply_time_decay private method.

    These tests verify the decay formula by testing through calculate_factors
    with raw buckets at different dates.
    """

    def test_no_decay_for_today(self, calculator: FairShareFactorCalculator, today: date) -> None:
        """Usage from today should not be decayed."""
        domain_name = "test-domain"
        usage = ResourceSlot({"cpu": Decimal("1000"), "mem": Decimal("2000")})

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={domain_name: {today: usage}},
                project={},
                user={},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # No decay for today's bucket - total_decayed_usage should equal original
        assert result.domain_results[domain_name].total_decayed_usage["cpu"] == Decimal("1000")
        assert result.domain_results[domain_name].total_decayed_usage["mem"] == Decimal("2000")

    def test_half_decay_at_half_life(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Usage should decay to 50% at half_life_days."""
        domain_name = "test-domain"
        usage = ResourceSlot({"cpu": Decimal("1000")})
        bucket_date = date(2024, 1, 8)  # 7 days ago

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={domain_name: {bucket_date: usage}},
                project={},
                user={},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # 2^(-7/7) = 2^(-1) = 0.5
        assert result.domain_results[domain_name].total_decayed_usage["cpu"] == Decimal("500")

    def test_quarter_decay_at_double_half_life(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Usage should decay to 25% at 2x half_life_days."""
        domain_name = "test-domain"
        usage = ResourceSlot({"cpu": Decimal("1000")})
        bucket_date = date(2024, 1, 1)  # 14 days ago

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={domain_name: {bucket_date: usage}},
                project={},
                user={},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # 2^(-14/7) = 2^(-2) = 0.25
        assert result.domain_results[domain_name].total_decayed_usage["cpu"] == Decimal("250")

    def test_multiple_buckets_aggregated_with_decay(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Multiple date buckets should be aggregated after individual decay."""
        domain_name = "test-domain"

        # Two buckets: today (no decay) and 7 days ago (50% decay)
        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={
                    domain_name: {
                        today: ResourceSlot({"cpu": Decimal("1000")}),  # 1000 (no decay)
                        date(2024, 1, 8): ResourceSlot({"cpu": Decimal("1000")}),  # 500 (50% decay)
                    }
                },
                project={},
                user={},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # Total: 1000 + 500 = 1500
        assert result.domain_results[domain_name].total_decayed_usage["cpu"] == Decimal("1500")

    def test_different_half_life_values(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Different half_life_days should produce different decay rates."""
        domain_name = "test-domain"
        usage = ResourceSlot({"cpu": Decimal("1000")})
        bucket_date = date(2024, 1, 8)  # 7 days ago

        # half_life=7: 50% decay
        context_7 = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={domain_name: {bucket_date: usage}},
                project={},
                user={},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        # half_life=14: less decay (7 days is only half the half-life)
        context_14 = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={domain_name: {bucket_date: usage}},
                project={},
                user={},
            ),
            half_life_days=14,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result_7 = calculator.calculate_factors(context_7)
        result_14 = calculator.calculate_factors(context_14)

        assert result_7.domain_results[domain_name].total_decayed_usage["cpu"] == Decimal("500")
        # 2^(-7/14) = 2^(-0.5) ≈ 0.707
        expected_14 = Decimal("1000") * (Decimal("2") ** (Decimal("-7") / Decimal("14")))
        actual_14 = result_14.domain_results[domain_name].total_decayed_usage["cpu"]
        assert abs(actual_14 - expected_14) < Decimal("0.01")


class TestCalculateUsageScore:
    """Tests for _calculate_usage_score method."""

    def test_single_resource_with_weight(self, calculator: FairShareFactorCalculator) -> None:
        """Single resource weighted correctly."""
        usage = ResourceSlot({"cpu": Decimal("1000")})
        weights = ResourceSlot({"cpu": Decimal("2.0")})

        score = calculator._calculate_usage_score(usage, weights)

        # 1000 * 2.0 / 2.0 = 1000 (normalized by total weight)
        assert score == Decimal("1000")

    def test_multiple_resources_weighted_average(
        self, calculator: FairShareFactorCalculator
    ) -> None:
        """Multiple resources combined with weighted average."""
        usage = ResourceSlot({"cpu": Decimal("1000"), "mem": Decimal("2000")})
        weights = ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")})

        score = calculator._calculate_usage_score(usage, weights)

        # (1000*1.0 + 2000*1.0) / (1.0 + 1.0) = 1500
        assert score == Decimal("1500")

    def test_different_weights_affect_score(self, calculator: FairShareFactorCalculator) -> None:
        """Different weights should affect the final score."""
        usage = ResourceSlot({"cpu": Decimal("1000"), "mem": Decimal("1000000")})

        # Equal weights
        weights_equal = ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("1.0")})
        score_equal = calculator._calculate_usage_score(usage, weights_equal)

        # mem weight much lower (like bytes vs cores)
        weights_scaled = ResourceSlot({"cpu": Decimal("1.0"), "mem": Decimal("0.001")})
        score_scaled = calculator._calculate_usage_score(usage, weights_scaled)

        # score_scaled should be much smaller due to mem being weighted down
        assert score_scaled < score_equal

    def test_empty_usage_returns_zero(self, calculator: FairShareFactorCalculator) -> None:
        """Empty usage should return zero score."""
        usage = ResourceSlot()
        weights = ResourceSlot({"cpu": Decimal("1.0")})

        score = calculator._calculate_usage_score(usage, weights)

        assert score == Decimal("0")

    def test_missing_weight_uses_default(self, calculator: FairShareFactorCalculator) -> None:
        """Resources without explicit weight use default of 1.0."""
        usage = ResourceSlot({"cpu": Decimal("1000"), "custom": Decimal("500")})
        weights = ResourceSlot({"cpu": Decimal("1.0")})  # No weight for 'custom'

        score = calculator._calculate_usage_score(usage, weights)

        # (1000*1.0 + 500*1.0) / (1.0 + 1.0) = 750
        assert score == Decimal("750")


class TestCalculateFactor:
    """Tests for _calculate_factor method."""

    def test_zero_usage_returns_factor_one(self, calculator: FairShareFactorCalculator) -> None:
        """Zero usage should give maximum factor (1.0)."""
        usage = ResourceSlot()
        weight = Decimal("1.0")
        resource_weights = ResourceSlot({"cpu": Decimal("1.0")})
        time_capacity = Decimal("604800")  # 7 days in seconds

        normalized, factor = calculator._calculate_factor(
            usage, weight, resource_weights, time_capacity
        )

        assert normalized == Decimal("0")
        assert factor == Decimal("1")  # 2^0 = 1

    def test_usage_equals_weight_gives_half_factor(
        self, calculator: FairShareFactorCalculator
    ) -> None:
        """When normalized_usage equals weight, factor should be 0.5."""
        # Setup: normalized_usage = usage_score / time_capacity = weight
        # So: usage_score = weight * time_capacity
        weight = Decimal("1.0")
        time_capacity = Decimal("604800")
        usage_score = weight * time_capacity  # Makes normalized_usage = weight

        # cpu * cpu_weight / total_weight = usage_score
        # cpu * 1.0 / 1.0 = usage_score
        usage = ResourceSlot({"cpu": usage_score})
        resource_weights = ResourceSlot({"cpu": Decimal("1.0")})

        normalized, factor = calculator._calculate_factor(
            usage, weight, resource_weights, time_capacity
        )

        # F = 2^(-1) = 0.5
        assert normalized == weight
        assert factor == Decimal("0.5")

    def test_higher_weight_gives_higher_factor(self, calculator: FairShareFactorCalculator) -> None:
        """Higher weight should result in higher factor for same usage."""
        usage = ResourceSlot({"cpu": Decimal("604800")})  # Makes normalized=1 with time_cap
        resource_weights = ResourceSlot({"cpu": Decimal("1.0")})
        time_capacity = Decimal("604800")

        _, factor_low_weight = calculator._calculate_factor(
            usage, Decimal("1.0"), resource_weights, time_capacity
        )
        _, factor_high_weight = calculator._calculate_factor(
            usage, Decimal("2.0"), resource_weights, time_capacity
        )

        # Higher weight = less penalty = higher factor
        assert factor_high_weight > factor_low_weight

    def test_factor_clamped_to_valid_range(self, calculator: FairShareFactorCalculator) -> None:
        """Factor should be clamped to [0, 1] range."""
        resource_weights = ResourceSlot({"cpu": Decimal("1.0")})
        time_capacity = Decimal("604800")
        weight = Decimal("1.0")

        # Very high usage should give factor close to 0
        high_usage = ResourceSlot({"cpu": Decimal("100000000")})
        _, factor_high = calculator._calculate_factor(
            high_usage, weight, resource_weights, time_capacity
        )
        assert factor_high >= Decimal("0")
        assert factor_high <= Decimal("1")

        # Zero usage should give factor = 1
        zero_usage = ResourceSlot()
        _, factor_zero = calculator._calculate_factor(
            zero_usage, weight, resource_weights, time_capacity
        )
        assert factor_zero == Decimal("1")


class TestCalculateFactors:
    """Tests for calculate_factors method - integration tests."""

    def test_empty_usages_returns_empty_results(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Empty raw usage buckets should return empty results."""
        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(domain={}, project={}, user={}),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        assert len(result.domain_results) == 0
        assert len(result.project_results) == 0
        assert len(result.user_results) == 0
        assert len(result.scheduling_ranks) == 0

    def test_calculates_all_levels(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Should calculate factors for domain, project, and user levels."""
        domain_name = "test-domain"
        project_id = uuid4()
        user_uuid = uuid4()
        user_key = UserProjectKey(user_uuid, project_id)

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(
                domain={
                    domain_name: DomainFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        domain_name=domain_name,
                        spec=make_fair_share_spec(weight=Decimal("1.0")),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    )
                },
                project={
                    project_id: ProjectFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        project_id=project_id,
                        domain_name=domain_name,
                        spec=make_fair_share_spec(weight=Decimal("1.0")),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    )
                },
                user={
                    user_key: UserFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        user_uuid=user_uuid,
                        project_id=project_id,
                        domain_name=domain_name,
                        spec=make_fair_share_spec(weight=Decimal("1.0")),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    )
                },
            ),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={domain_name: {today: ResourceSlot({"cpu": Decimal("1000")})}},
                project={project_id: {today: ResourceSlot({"cpu": Decimal("1000")})}},
                user={user_key: {today: ResourceSlot({"cpu": Decimal("1000")})}},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        assert len(result.domain_results) == 1
        assert len(result.project_results) == 1
        assert len(result.user_results) == 1
        assert domain_name in result.domain_results
        assert project_id in result.project_results
        assert user_key in result.user_results

    def test_half_life_affects_factor(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Different half_life_days should produce different factors."""
        domain_name = "test-domain"
        # Usage from today (no decay)
        raw_buckets = RawUsageBucketsByLevel(
            domain={domain_name: {today: ResourceSlot({"cpu": Decimal("604800")})}},
            project={},
            user={},
        )

        # Short half-life: smaller time_capacity -> higher normalized_usage -> lower factor
        context_short = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=raw_buckets,
            half_life_days=3,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        # Long half-life: larger time_capacity -> lower normalized_usage -> higher factor
        context_long = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=raw_buckets,
            half_life_days=14,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result_short = calculator.calculate_factors(context_short)
        result_long = calculator.calculate_factors(context_long)

        factor_short = result_short.domain_results[domain_name].fair_share_factor
        factor_long = result_long.domain_results[domain_name].fair_share_factor

        # Shorter half-life = smaller time_capacity = larger normalized_usage = lower factor
        assert factor_short < factor_long

    def test_weight_affects_factor(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Higher weight should give higher factor for same usage."""
        domain_name = "test-domain"
        raw_buckets = RawUsageBucketsByLevel(
            domain={domain_name: {today: ResourceSlot({"cpu": Decimal("604800")})}},
            project={},
            user={},
        )

        # Low weight
        context_low = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(
                domain={
                    domain_name: DomainFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        domain_name=domain_name,
                        spec=make_fair_share_spec(weight=Decimal("0.5")),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    )
                },
                project={},
                user={},
            ),
            raw_usage_buckets=raw_buckets,
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        # High weight
        context_high = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(
                domain={
                    domain_name: DomainFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        domain_name=domain_name,
                        spec=make_fair_share_spec(weight=Decimal("2.0")),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    )
                },
                project={},
                user={},
            ),
            raw_usage_buckets=raw_buckets,
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result_low = calculator.calculate_factors(context_low)
        result_high = calculator.calculate_factors(context_high)

        factor_low = result_low.domain_results[domain_name].fair_share_factor
        factor_high = result_high.domain_results[domain_name].fair_share_factor

        # Higher weight = less penalty = higher factor
        assert factor_high > factor_low


class TestCalculateSchedulingRanks:
    """Tests for _calculate_scheduling_ranks method."""

    def test_empty_user_results_returns_empty(self, calculator: FairShareFactorCalculator) -> None:
        """Empty user results should return empty ranks."""
        from ai.backend.manager.sokovan.scheduler.fair_share.calculator import (
            FairShareFactorCalculationResult,
        )

        result = FairShareFactorCalculationResult()
        ranks = calculator._calculate_scheduling_ranks(result)

        assert len(ranks) == 0

    def test_single_user_gets_rank_one(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Single user should get rank 1."""
        user_key = UserProjectKey(uuid4(), uuid4())

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={},
                project={},
                user={user_key: {today: ResourceSlot({"cpu": Decimal("1000")})}},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        assert len(result.scheduling_ranks) == 1
        assert result.scheduling_ranks[0].rank == 1
        assert result.scheduling_ranks[0].user_uuid == user_key.user_uuid
        assert result.scheduling_ranks[0].project_id == user_key.project_id

    def test_higher_factor_gets_lower_rank(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """User with higher factor (less usage) should get lower rank (higher priority)."""
        user1_key = UserProjectKey(uuid4(), uuid4())
        user2_key = UserProjectKey(uuid4(), uuid4())

        # User1 has more usage -> lower factor -> higher rank number
        # User2 has less usage -> higher factor -> lower rank number (higher priority)
        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={},
                project={},
                user={
                    user1_key: {today: ResourceSlot({"cpu": Decimal("10000000")})},  # High usage
                    user2_key: {today: ResourceSlot({"cpu": Decimal("100")})},  # Low usage
                },
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # Find ranks for each user
        user1_rank = next(r for r in result.scheduling_ranks if r.user_uuid == user1_key.user_uuid)
        user2_rank = next(r for r in result.scheduling_ranks if r.user_uuid == user2_key.user_uuid)

        # User2 (less usage) should have lower rank (higher priority)
        assert user2_rank.rank < user1_rank.rank

    def test_multiple_users_ranked_correctly(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Multiple users should be ranked in order of factor (descending)."""
        users = [
            (UserProjectKey(uuid4(), uuid4()), Decimal("100")),  # Lowest usage -> rank 1
            (UserProjectKey(uuid4(), uuid4()), Decimal("1000")),  # Medium usage -> rank 2
            (UserProjectKey(uuid4(), uuid4()), Decimal("10000")),  # High usage -> rank 3
            (UserProjectKey(uuid4(), uuid4()), Decimal("100000")),  # Highest usage -> rank 4
        ]

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={},
                project={},
                user={key: {today: ResourceSlot({"cpu": usage})} for key, usage in users},
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # Verify we have 4 ranks
        assert len(result.scheduling_ranks) == 4

        # Build expected order (lowest usage first)
        expected_order = [key for key, _ in users]

        # Verify ranks are assigned correctly
        for expected_rank, expected_key in enumerate(expected_order, start=1):
            actual_rank = next(
                r for r in result.scheduling_ranks if r.user_uuid == expected_key.user_uuid
            )
            assert actual_rank.rank == expected_rank, (
                f"User with usage index {expected_rank - 1} should have rank {expected_rank}, "
                f"got {actual_rank.rank}"
            )


class TestIntegrationScenarios:
    """Integration tests for realistic fair share scenarios."""

    def test_recent_vs_old_usage_priority(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """User with recent usage should have lower priority than user with old usage.

        This tests the full flow: different bucket dates -> different decayed usage
        -> different factors -> different ranks.
        """
        user_recent_key = UserProjectKey(uuid4(), uuid4())
        user_old_key = UserProjectKey(uuid4(), uuid4())

        # Both users have same raw usage (1000 cpu-seconds), but at different dates
        raw_usage = ResourceSlot({"cpu": Decimal("1000")})
        old_date = date(2024, 1, 1)  # 14 days ago - 75% decayed

        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(domain={}, project={}, user={}),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={},
                project={},
                user={
                    user_recent_key: {today: raw_usage},  # 1000 (no decay)
                    user_old_key: {old_date: raw_usage},  # 250 (75% decayed)
                },
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # User with old (decayed) usage should have higher factor
        factor_recent = result.user_results[user_recent_key].fair_share_factor
        factor_old = result.user_results[user_old_key].fair_share_factor
        assert factor_old > factor_recent

        # User with old usage should have lower rank (higher priority)
        rank_recent = next(
            r for r in result.scheduling_ranks if r.user_uuid == user_recent_key.user_uuid
        )
        rank_old = next(r for r in result.scheduling_ranks if r.user_uuid == user_old_key.user_uuid)
        assert rank_old.rank < rank_recent.rank

    def test_domain_project_user_hierarchy_affects_rank(
        self, calculator: FairShareFactorCalculator, today: date
    ) -> None:
        """Ranking should consider domain and project factors, not just user factor."""
        domain_a = "domain-a"
        domain_b = "domain-b"
        project_a = uuid4()
        project_b = uuid4()
        user_a = UserProjectKey(uuid4(), project_a)
        user_b = UserProjectKey(uuid4(), project_b)

        # User A: low personal usage, but domain has high usage
        # User B: high personal usage, but domain has low usage
        context = FairShareCalculationContext(
            fair_shares=FairSharesByLevel(
                domain={
                    domain_a: DomainFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        domain_name=domain_a,
                        spec=make_fair_share_spec(),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    ),
                    domain_b: DomainFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        domain_name=domain_b,
                        spec=make_fair_share_spec(),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    ),
                },
                project={
                    project_a: ProjectFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        project_id=project_a,
                        domain_name=domain_a,
                        spec=make_fair_share_spec(),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    ),
                    project_b: ProjectFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        project_id=project_b,
                        domain_name=domain_b,
                        spec=make_fair_share_spec(),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    ),
                },
                user={
                    user_a: UserFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        user_uuid=user_a.user_uuid,
                        project_id=project_a,
                        domain_name=domain_a,
                        spec=make_fair_share_spec(),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    ),
                    user_b: UserFairShareData(
                        id=uuid4(),
                        resource_group="default",
                        user_uuid=user_b.user_uuid,
                        project_id=project_b,
                        domain_name=domain_b,
                        spec=make_fair_share_spec(),
                        calculation_snapshot=make_calculation_snapshot(),
                        metadata=make_metadata(),
                    ),
                },
            ),
            raw_usage_buckets=RawUsageBucketsByLevel(
                domain={
                    # High domain usage for domain_a
                    domain_a: {today: ResourceSlot({"cpu": Decimal("100000000")})},
                    # Low domain usage for domain_b
                    domain_b: {today: ResourceSlot({"cpu": Decimal("100")})},
                },
                project={
                    project_a: {today: ResourceSlot({"cpu": Decimal("10000000")})},
                    project_b: {today: ResourceSlot({"cpu": Decimal("100")})},
                },
                user={
                    # User A: low personal usage
                    user_a: {today: ResourceSlot({"cpu": Decimal("100")})},
                    # User B: high personal usage
                    user_b: {today: ResourceSlot({"cpu": Decimal("10000")})},
                },
            ),
            half_life_days=7,
            lookback_days=30,
            default_weight=Decimal("1.0"),
            resource_weights=ResourceSlot({"cpu": Decimal("1.0")}),
            today=today,
        )

        result = calculator.calculate_factors(context)

        # Domain B has much lower usage -> higher domain factor
        # Even though User B has higher personal usage, Domain B's advantage should help
        rank_a = next(r for r in result.scheduling_ranks if r.user_uuid == user_a.user_uuid)
        rank_b = next(r for r in result.scheduling_ranks if r.user_uuid == user_b.user_uuid)

        # User B (in low-usage domain) should have better rank despite higher personal usage
        assert rank_b.rank < rank_a.rank
