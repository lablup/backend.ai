"""Tests for FairShareAggregator bucket aggregation logic.

Verifies that kernel usage specs are correctly split by day boundaries
and aggregated into user/project/domain buckets.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.repositories.resource_usage_history import (
    KernelUsageRecordCreatorSpec,
)
from ai.backend.manager.sokovan.scheduler.fair_share.aggregator import (
    DomainUsageBucketKey,
    FairShareAggregator,
    ProjectUsageBucketKey,
    UserUsageBucketKey,
)


def make_datetime(
    year: int, month: int, day: int, hour: int, minute: int, second: int = 0
) -> datetime:
    """Create a datetime with timezone for testing."""
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def make_spec(
    period_start: datetime,
    period_end: datetime,
    resource_usage: ResourceSlot,
    user_uuid: UUID | None = None,
    project_id: UUID | None = None,
    domain_name: str = "default",
    resource_group: str = "default",
) -> KernelUsageRecordCreatorSpec:
    """Create a KernelUsageRecordCreatorSpec for testing."""
    return KernelUsageRecordCreatorSpec(
        kernel_id=uuid4(),
        session_id=uuid4(),
        user_uuid=user_uuid or uuid4(),
        project_id=project_id or uuid4(),
        domain_name=domain_name,
        resource_group=resource_group,
        period_start=period_start,
        period_end=period_end,
        resource_usage=resource_usage,
    )


@pytest.fixture
def aggregator() -> FairShareAggregator:
    """Create FairShareAggregator - no mocks needed (pure computation)."""
    return FairShareAggregator()


class TestSplitSpecByDay:
    """Tests for _split_spec_by_day method."""

    def test_spec_within_single_day(self, aggregator: FairShareAggregator) -> None:
        """Spec entirely within one day should not be split."""
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 10, 0, 0),
            period_end=make_datetime(2024, 1, 15, 10, 5, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 2 CPU * 300s
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 1
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1]["cpu"] == Decimal("600")

    def test_spec_crossing_midnight(self, aggregator: FairShareAggregator) -> None:
        """Spec crossing midnight should be split proportionally."""
        # 23:57 ~ 00:03 (6 minutes total)
        # Day 1: 23:57 ~ 00:00 = 3 minutes (50%)
        # Day 2: 00:00 ~ 00:03 = 3 minutes (50%)
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 57, 0),
            period_end=make_datetime(2024, 1, 16, 0, 3, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("720")}),  # 2 CPU * 360s
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 2

        # Day 1: 2024-01-15, 50% of usage
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1]["cpu"] == Decimal("360")  # 720 * 0.5

        # Day 2: 2024-01-16, 50% of usage
        assert result[1][0] == date(2024, 1, 16)
        assert result[1][1]["cpu"] == Decimal("360")  # 720 * 0.5

    def test_spec_crossing_midnight_uneven_split(self, aggregator: FairShareAggregator) -> None:
        """Spec crossing midnight with uneven time distribution."""
        # 23:58 ~ 00:02 (4 minutes total)
        # Day 1: 23:58 ~ 00:00 = 2 minutes (50%)
        # Day 2: 00:00 ~ 00:02 = 2 minutes (50%)
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 58, 0),
            period_end=make_datetime(2024, 1, 16, 0, 2, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("480"), "mem": Decimal("960")}),
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 2
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1]["cpu"] == Decimal("240")
        assert result[0][1]["mem"] == Decimal("480")

        assert result[1][0] == date(2024, 1, 16)
        assert result[1][1]["cpu"] == Decimal("240")
        assert result[1][1]["mem"] == Decimal("480")

    def test_spec_empty_range(self, aggregator: FairShareAggregator) -> None:
        """Spec with zero duration should return empty list."""
        same_time = make_datetime(2024, 1, 15, 12, 0, 0)
        spec = make_spec(
            period_start=same_time,
            period_end=same_time,
            resource_usage=ResourceSlot({"cpu": Decimal("0")}),
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 0


class TestAggregateKernelUsageToBuckets:
    """Tests for aggregate_kernel_usage_to_buckets method."""

    def test_single_spec_single_day(self, aggregator: FairShareAggregator) -> None:
        """Single spec within one day creates one bucket entry per level."""
        user_uuid = uuid4()
        project_id = uuid4()

        specs = [
            make_spec(
                period_start=make_datetime(2024, 1, 15, 10, 0, 0),
                period_end=make_datetime(2024, 1, 15, 10, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                user_uuid=user_uuid,
                project_id=project_id,
                domain_name="test-domain",
                resource_group="test-rg",
            )
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        # User bucket
        assert len(result.user_usage_deltas) == 1
        user_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="test-domain",
            resource_group="test-rg",
            period_date=date(2024, 1, 15),
        )
        assert user_key in result.user_usage_deltas
        assert result.user_usage_deltas[user_key]["cpu"] == Decimal("600")

        # Project bucket
        assert len(result.project_usage_deltas) == 1
        project_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="test-domain",
            resource_group="test-rg",
            period_date=date(2024, 1, 15),
        )
        assert project_key in result.project_usage_deltas
        assert result.project_usage_deltas[project_key]["cpu"] == Decimal("600")

        # Domain bucket
        assert len(result.domain_usage_deltas) == 1
        domain_key = DomainUsageBucketKey(
            domain_name="test-domain",
            resource_group="test-rg",
            period_date=date(2024, 1, 15),
        )
        assert domain_key in result.domain_usage_deltas
        assert result.domain_usage_deltas[domain_key]["cpu"] == Decimal("600")

    def test_multiple_specs_same_user_same_day_aggregated(
        self, aggregator: FairShareAggregator
    ) -> None:
        """Multiple specs from same user on same day are aggregated."""
        user_uuid = uuid4()
        project_id = uuid4()

        specs = [
            make_spec(
                period_start=make_datetime(2024, 1, 15, 10, 0, 0),
                period_end=make_datetime(2024, 1, 15, 10, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 10, 5, 0),
                period_end=make_datetime(2024, 1, 15, 10, 10, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        # Should have only one user bucket with summed usage
        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        assert result.user_usage_deltas[user_key]["cpu"] == Decimal("1200")

    def test_spec_crossing_midnight_creates_two_buckets(
        self, aggregator: FairShareAggregator
    ) -> None:
        """Spec crossing midnight creates buckets for both days."""
        user_uuid = uuid4()
        project_id = uuid4()

        # 23:57 ~ 00:03 (6 minutes, split evenly)
        specs = [
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 57, 0),
                period_end=make_datetime(2024, 1, 16, 0, 3, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("720")}),
                user_uuid=user_uuid,
                project_id=project_id,
            )
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        # Should have two user buckets (one per day)
        assert len(result.user_usage_deltas) == 2

        day1_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 15),
        )
        day2_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 16),
        )

        assert day1_key in result.user_usage_deltas
        assert day2_key in result.user_usage_deltas
        assert result.user_usage_deltas[day1_key]["cpu"] == Decimal("360")
        assert result.user_usage_deltas[day2_key]["cpu"] == Decimal("360")


class TestBackloggedUsageScenario:
    """
    Tests for backlogged usage scenario.

    Scenario: Observer was delayed and received usage data from 23:36 to 00:13.
    This simulates a situation where the 5-minute observation cycle was delayed
    and multiple slices arrived at once, spanning midnight.

    Timeline (37 minutes total):
    - 23:36 ~ 23:40 (4min, partial start) -> Day 1
    - 23:40 ~ 23:45 (5min) -> Day 1
    - 23:45 ~ 23:50 (5min) -> Day 1
    - 23:50 ~ 23:55 (5min) -> Day 1
    - 23:55 ~ 00:00 (5min) -> Day 1
    - 00:00 ~ 00:05 (5min) -> Day 2
    - 00:05 ~ 00:10 (5min) -> Day 2
    - 00:10 ~ 00:13 (3min, partial end) -> Day 2

    Day 1 total: 4 + 5 + 5 + 5 + 5 = 24 minutes
    Day 2 total: 5 + 5 + 3 = 13 minutes
    """

    def test_backlogged_usage_split_correctly(self, aggregator: FairShareAggregator) -> None:
        """Backlogged usage spanning midnight is correctly split by day."""
        user_uuid = uuid4()
        project_id = uuid4()
        cpu_per_second = Decimal("2")  # 2 CPU cores

        # Simulate specs that would be generated from 23:36 to 00:13
        specs = [
            # Day 1 specs
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 36, 0),
                period_end=make_datetime(2024, 1, 15, 23, 40, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 240}),  # 4min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 40, 0),
                period_end=make_datetime(2024, 1, 15, 23, 45, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),  # 5min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 45, 0),
                period_end=make_datetime(2024, 1, 15, 23, 50, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),  # 5min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 50, 0),
                period_end=make_datetime(2024, 1, 15, 23, 55, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),  # 5min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 55, 0),
                period_end=make_datetime(2024, 1, 16, 0, 0, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),  # 5min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            # Day 2 specs
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 0, 0),
                period_end=make_datetime(2024, 1, 16, 0, 5, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),  # 5min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 5, 0),
                period_end=make_datetime(2024, 1, 16, 0, 10, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),  # 5min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 10, 0),
                period_end=make_datetime(2024, 1, 16, 0, 13, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 180}),  # 3min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        # Should have exactly 2 user buckets (one per day)
        assert len(result.user_usage_deltas) == 2

        day1_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 15),
        )
        day2_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 16),
        )

        # Day 1: 24 minutes = 1440 seconds, 2 CPU = 2880 cpu-seconds
        day1_expected = cpu_per_second * (240 + 300 + 300 + 300 + 300)  # 1440s * 2
        assert result.user_usage_deltas[day1_key]["cpu"] == day1_expected
        assert day1_expected == Decimal("2880")

        # Day 2: 13 minutes = 780 seconds, 2 CPU = 1560 cpu-seconds
        day2_expected = cpu_per_second * (300 + 300 + 180)  # 780s * 2
        assert result.user_usage_deltas[day2_key]["cpu"] == day2_expected
        assert day2_expected == Decimal("1560")

    def test_backlogged_usage_with_midnight_crossing_spec(
        self, aggregator: FairShareAggregator
    ) -> None:
        """Backlogged usage where one spec crosses midnight."""
        user_uuid = uuid4()
        project_id = uuid4()
        cpu_per_second = Decimal("2")

        # Scenario: observation was very delayed, and one slice spans midnight
        # 23:36 ~ 00:13 treated as continuous period (unlikely but possible edge case)
        # More realistic: 23:57 ~ 00:02 slice that crosses midnight
        specs = [
            # Earlier Day 1 specs
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 36, 0),
                period_end=make_datetime(2024, 1, 15, 23, 40, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 240}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 40, 0),
                period_end=make_datetime(2024, 1, 15, 23, 45, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 45, 0),
                period_end=make_datetime(2024, 1, 15, 23, 50, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 50, 0),
                period_end=make_datetime(2024, 1, 15, 23, 55, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            # Spec crossing midnight: 23:55 ~ 00:05 (10 minutes)
            # Day 1: 5 minutes, Day 2: 5 minutes
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 55, 0),
                period_end=make_datetime(2024, 1, 16, 0, 5, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 600}),  # 10min
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            # Day 2 specs
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 5, 0),
                period_end=make_datetime(2024, 1, 16, 0, 10, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 10, 0),
                period_end=make_datetime(2024, 1, 16, 0, 13, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 180}),
                user_uuid=user_uuid,
                project_id=project_id,
            ),
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        assert len(result.user_usage_deltas) == 2

        day1_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 15),
        )
        day2_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 16),
        )

        # Day 1: 4 + 5 + 5 + 5 + 5 (from crossing spec) = 24 minutes = 1440s
        # cpu-seconds: 1440 * 2 = 2880
        day1_expected = cpu_per_second * (240 + 300 + 300 + 300 + 300)
        assert result.user_usage_deltas[day1_key]["cpu"] == day1_expected

        # Day 2: 5 (from crossing spec) + 5 + 3 = 13 minutes = 780s
        # cpu-seconds: 780 * 2 = 1560
        day2_expected = cpu_per_second * (300 + 300 + 180)
        assert result.user_usage_deltas[day2_key]["cpu"] == day2_expected

    def test_backlogged_multiple_users(self, aggregator: FairShareAggregator) -> None:
        """Backlogged usage from multiple users is correctly separated."""
        user1_uuid = uuid4()
        user2_uuid = uuid4()
        project_id = uuid4()
        cpu_per_second = Decimal("2")

        specs = [
            # User 1: Day 1 only
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 40, 0),
                period_end=make_datetime(2024, 1, 15, 23, 45, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 300}),
                user_uuid=user1_uuid,
                project_id=project_id,
            ),
            # User 2: spans both days
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 55, 0),
                period_end=make_datetime(2024, 1, 16, 0, 5, 0),
                resource_usage=ResourceSlot({"cpu": cpu_per_second * 600}),
                user_uuid=user2_uuid,
                project_id=project_id,
            ),
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        # User buckets: user1 day1, user2 day1, user2 day2 = 3 buckets
        assert len(result.user_usage_deltas) == 3

        # Project buckets: day1 (both users), day2 (user2 only) = 2 buckets
        assert len(result.project_usage_deltas) == 2

        # Verify project aggregation sums both users on day 1
        project_day1_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 15),
        )
        # User1: 300*2=600, User2: 300*2=600 (half of crossing spec)
        assert result.project_usage_deltas[project_day1_key]["cpu"] == Decimal("1200")

        project_day2_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 16),
        )
        # User2 only: 300*2=600 (half of crossing spec)
        assert result.project_usage_deltas[project_day2_key]["cpu"] == Decimal("600")


class TestEdgeCases:
    """Edge case tests for bucket aggregation."""

    def test_empty_specs_list(self, aggregator: FairShareAggregator) -> None:
        """Empty specs list returns empty result."""
        result = aggregator.aggregate_kernel_usage_to_buckets([])

        assert len(result.user_usage_deltas) == 0
        assert len(result.project_usage_deltas) == 0
        assert len(result.domain_usage_deltas) == 0

    def test_spec_exactly_at_midnight_boundary(self, aggregator: FairShareAggregator) -> None:
        """Spec ending exactly at midnight stays in single day."""
        user_uuid = uuid4()
        project_id = uuid4()

        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 55, 0),
            period_end=make_datetime(2024, 1, 16, 0, 0, 0),  # Exactly midnight
            resource_usage=ResourceSlot({"cpu": Decimal("600")}),
            user_uuid=user_uuid,
            project_id=project_id,
        )

        result = aggregator.aggregate_kernel_usage_to_buckets([spec])

        # Should be entirely in Day 1 (end is exclusive boundary)
        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        assert user_key.period_date == date(2024, 1, 15)
        assert result.user_usage_deltas[user_key]["cpu"] == Decimal("600")

    def test_spec_starting_exactly_at_midnight(self, aggregator: FairShareAggregator) -> None:
        """Spec starting exactly at midnight is in the new day."""
        user_uuid = uuid4()
        project_id = uuid4()

        spec = make_spec(
            period_start=make_datetime(2024, 1, 16, 0, 0, 0),  # Exactly midnight
            period_end=make_datetime(2024, 1, 16, 0, 5, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("600")}),
            user_uuid=user_uuid,
            project_id=project_id,
        )

        result = aggregator.aggregate_kernel_usage_to_buckets([spec])

        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        assert user_key.period_date == date(2024, 1, 16)

    def test_multiple_resource_types(self, aggregator: FairShareAggregator) -> None:
        """Multiple resource types are all split proportionally."""
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 58, 0),
            period_end=make_datetime(2024, 1, 16, 0, 2, 0),  # 4 minutes, 50/50 split
            resource_usage=ResourceSlot({
                "cpu": Decimal("480"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("200"),
            }),
        )

        result = aggregator.aggregate_kernel_usage_to_buckets([spec])

        assert len(result.user_usage_deltas) == 2

        for key, usage in result.user_usage_deltas.items():
            # Each day gets 50%
            assert usage["cpu"] == Decimal("240")
            assert usage["mem"] == Decimal("4096")
            assert usage["cuda.shares"] == Decimal("100")
