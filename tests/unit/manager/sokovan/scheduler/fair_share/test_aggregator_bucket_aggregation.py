"""Tests for FairShareAggregator bucket aggregation logic.

Verifies that kernel usage specs are correctly split by day boundaries
and aggregated into user/project/domain buckets.

Phase 3 (BA-4308): BucketDelta stores raw amount and duration separately.
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
    occupied_slots: ResourceSlot | None = None,
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
        occupied_slots=occupied_slots,
    )


@pytest.fixture
def aggregator() -> FairShareAggregator:
    """Create FairShareAggregator - no mocks needed (pure computation)."""
    return FairShareAggregator()


class TestSplitSpecByDay:
    """Tests for _split_spec_by_day method.

    _split_spec_by_day returns (date, raw_slots, segment_seconds) tuples.
    """

    def test_spec_within_single_day(self, aggregator: FairShareAggregator) -> None:
        """Spec entirely within one day should not be split."""
        raw_slots = ResourceSlot({"cpu": Decimal("2")})
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 10, 0, 0),
            period_end=make_datetime(2024, 1, 15, 10, 5, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 2 CPU * 300s
            occupied_slots=raw_slots,
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 1
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1]["cpu"] == Decimal("2")  # raw amount
        assert result[0][2] == 300  # 5 minutes in seconds

    def test_spec_crossing_midnight(self, aggregator: FairShareAggregator) -> None:
        """Spec crossing midnight should be split by duration."""
        raw_slots = ResourceSlot({"cpu": Decimal("2")})
        # 23:57 ~ 00:03 (6 minutes total)
        # Day 1: 23:57 ~ 00:00 = 3 minutes (180s)
        # Day 2: 00:00 ~ 00:03 = 3 minutes (180s)
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 57, 0),
            period_end=make_datetime(2024, 1, 16, 0, 3, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("720")}),  # 2 CPU * 360s
            occupied_slots=raw_slots,
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 2

        # Day 1: 2024-01-15, raw slots + 180 seconds
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1]["cpu"] == Decimal("2")
        assert result[0][2] == 180

        # Day 2: 2024-01-16, raw slots + 180 seconds
        assert result[1][0] == date(2024, 1, 16)
        assert result[1][1]["cpu"] == Decimal("2")
        assert result[1][2] == 180

    def test_spec_crossing_midnight_uneven_split(self, aggregator: FairShareAggregator) -> None:
        """Spec crossing midnight with uneven time distribution."""
        raw_slots = ResourceSlot({"cpu": Decimal("2"), "mem": Decimal("4096")})
        # 23:58 ~ 00:02 (4 minutes total)
        # Day 1: 23:58 ~ 00:00 = 2 minutes (120s)
        # Day 2: 00:00 ~ 00:02 = 2 minutes (120s)
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 58, 0),
            period_end=make_datetime(2024, 1, 16, 0, 2, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("480"), "mem": Decimal("960")}),
            occupied_slots=raw_slots,
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 2
        assert result[0][0] == date(2024, 1, 15)
        assert result[0][1]["cpu"] == Decimal("2")
        assert result[0][1]["mem"] == Decimal("4096")
        assert result[0][2] == 120

        assert result[1][0] == date(2024, 1, 16)
        assert result[1][1]["cpu"] == Decimal("2")
        assert result[1][1]["mem"] == Decimal("4096")
        assert result[1][2] == 120

    def test_spec_empty_range(self, aggregator: FairShareAggregator) -> None:
        """Spec with zero duration should return empty list."""
        same_time = make_datetime(2024, 1, 15, 12, 0, 0)
        spec = make_spec(
            period_start=same_time,
            period_end=same_time,
            resource_usage=ResourceSlot({"cpu": Decimal("0")}),
            occupied_slots=ResourceSlot({"cpu": Decimal("2")}),
        )

        result = aggregator._split_spec_by_day(spec)

        assert len(result) == 0


class TestAggregateKernelUsageToBuckets:
    """Tests for aggregate_kernel_usage_to_buckets method.

    BucketDelta stores raw slots and duration_seconds separately.
    """

    def test_single_spec_single_day(self, aggregator: FairShareAggregator) -> None:
        """Single spec within one day creates one bucket entry per level."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        specs = [
            make_spec(
                period_start=make_datetime(2024, 1, 15, 10, 0, 0),
                period_end=make_datetime(2024, 1, 15, 10, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
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
        delta = result.user_usage_deltas[user_key]
        assert delta.slots["cpu"] == Decimal("2")
        assert delta.duration_seconds == 300

        # Project bucket
        assert len(result.project_usage_deltas) == 1
        project_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="test-domain",
            resource_group="test-rg",
            period_date=date(2024, 1, 15),
        )
        assert project_key in result.project_usage_deltas
        assert result.project_usage_deltas[project_key].slots["cpu"] == Decimal("2")

        # Domain bucket
        assert len(result.domain_usage_deltas) == 1
        domain_key = DomainUsageBucketKey(
            domain_name="test-domain",
            resource_group="test-rg",
            period_date=date(2024, 1, 15),
        )
        assert domain_key in result.domain_usage_deltas
        assert result.domain_usage_deltas[domain_key].slots["cpu"] == Decimal("2")

    def test_multiple_specs_same_user_same_day_aggregated(
        self, aggregator: FairShareAggregator
    ) -> None:
        """Multiple specs from same user on same day are aggregated."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        specs = [
            make_spec(
                period_start=make_datetime(2024, 1, 15, 10, 0, 0),
                period_end=make_datetime(2024, 1, 15, 10, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 10, 5, 0),
                period_end=make_datetime(2024, 1, 15, 10, 10, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        # Should have only one user bucket with summed raw slots and duration
        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        delta = result.user_usage_deltas[user_key]
        # Raw slots accumulate: 2 + 2 = 4
        assert delta.slots["cpu"] == Decimal("4")
        # Durations accumulate: 300 + 300 = 600
        assert delta.duration_seconds == 600

    def test_spec_crossing_midnight_creates_two_buckets(
        self, aggregator: FairShareAggregator
    ) -> None:
        """Spec crossing midnight creates buckets for both days."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        # 23:57 ~ 00:03 (6 minutes, split evenly)
        specs = [
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 57, 0),
                period_end=make_datetime(2024, 1, 16, 0, 3, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("720")}),
                occupied_slots=raw_slots,
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
        # Day 1: 3 minutes = 180s, raw slots = 2 CPU
        assert result.user_usage_deltas[day1_key].slots["cpu"] == Decimal("2")
        assert result.user_usage_deltas[day1_key].duration_seconds == 180
        # Day 2: 3 minutes = 180s, raw slots = 2 CPU
        assert result.user_usage_deltas[day2_key].slots["cpu"] == Decimal("2")
        assert result.user_usage_deltas[day2_key].duration_seconds == 180


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

    Day 1 total: 4 + 5 + 5 + 5 + 5 = 24 minutes = 1440 seconds
    Day 2 total: 5 + 5 + 3 = 13 minutes = 780 seconds
    """

    def test_backlogged_usage_split_correctly(self, aggregator: FairShareAggregator) -> None:
        """Backlogged usage spanning midnight is correctly split by day."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        # Simulate specs that would be generated from 23:36 to 00:13
        specs = [
            # Day 1 specs
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 36, 0),
                period_end=make_datetime(2024, 1, 15, 23, 40, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("480")}),  # 4min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 40, 0),
                period_end=make_datetime(2024, 1, 15, 23, 45, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 5min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 45, 0),
                period_end=make_datetime(2024, 1, 15, 23, 50, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 5min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 50, 0),
                period_end=make_datetime(2024, 1, 15, 23, 55, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 5min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 55, 0),
                period_end=make_datetime(2024, 1, 16, 0, 0, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 5min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            # Day 2 specs
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 0, 0),
                period_end=make_datetime(2024, 1, 16, 0, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 5min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 5, 0),
                period_end=make_datetime(2024, 1, 16, 0, 10, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),  # 5min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 10, 0),
                period_end=make_datetime(2024, 1, 16, 0, 13, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("360")}),  # 3min
                occupied_slots=raw_slots,
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

        # Day 1: 5 specs, raw_slots=2 each, accumulated = 2*5 = 10
        # duration: 240 + 300 + 300 + 300 + 300 = 1440 seconds
        d1 = result.user_usage_deltas[day1_key]
        assert d1.slots["cpu"] == Decimal("10")
        assert d1.duration_seconds == 1440

        # Day 2: 3 specs, raw_slots=2 each, accumulated = 2*3 = 6
        # duration: 300 + 300 + 180 = 780 seconds
        d2 = result.user_usage_deltas[day2_key]
        assert d2.slots["cpu"] == Decimal("6")
        assert d2.duration_seconds == 780

    def test_backlogged_usage_with_midnight_crossing_spec(
        self, aggregator: FairShareAggregator
    ) -> None:
        """Backlogged usage where one spec crosses midnight."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        specs = [
            # Earlier Day 1 specs
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 36, 0),
                period_end=make_datetime(2024, 1, 15, 23, 40, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("480")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 40, 0),
                period_end=make_datetime(2024, 1, 15, 23, 45, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 45, 0),
                period_end=make_datetime(2024, 1, 15, 23, 50, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 50, 0),
                period_end=make_datetime(2024, 1, 15, 23, 55, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            # Spec crossing midnight: 23:55 ~ 00:05 (10 minutes)
            # Day 1: 5 minutes (300s), Day 2: 5 minutes (300s)
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 55, 0),
                period_end=make_datetime(2024, 1, 16, 0, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("1200")}),  # 10min
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            # Day 2 specs
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 5, 0),
                period_end=make_datetime(2024, 1, 16, 0, 10, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            ),
            make_spec(
                period_start=make_datetime(2024, 1, 16, 0, 10, 0),
                period_end=make_datetime(2024, 1, 16, 0, 13, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("360")}),
                occupied_slots=raw_slots,
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

        # Day 1: specs contribute raw_slots=2 each
        # 4 complete specs + crossing spec day1 part = 5 contributions = 2*5 = 10
        # duration: 240 + 300 + 300 + 300 + 300(crossing) = 1440s
        d1 = result.user_usage_deltas[day1_key]
        assert d1.slots["cpu"] == Decimal("10")
        assert d1.duration_seconds == 1440

        # Day 2: crossing spec day2 part + 2 specs = 3 contributions = 2*3 = 6
        # duration: 300(crossing) + 300 + 180 = 780s
        d2 = result.user_usage_deltas[day2_key]
        assert d2.slots["cpu"] == Decimal("6")
        assert d2.duration_seconds == 780

    def test_backlogged_multiple_users(self, aggregator: FairShareAggregator) -> None:
        """Backlogged usage from multiple users is correctly separated."""
        user1_uuid = uuid4()
        user2_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        specs = [
            # User 1: Day 1 only
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 40, 0),
                period_end=make_datetime(2024, 1, 15, 23, 45, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("600")}),
                occupied_slots=raw_slots,
                user_uuid=user1_uuid,
                project_id=project_id,
            ),
            # User 2: spans both days (23:55 ~ 00:05)
            make_spec(
                period_start=make_datetime(2024, 1, 15, 23, 55, 0),
                period_end=make_datetime(2024, 1, 16, 0, 5, 0),
                resource_usage=ResourceSlot({"cpu": Decimal("1200")}),
                occupied_slots=raw_slots,
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
        # User1: raw=2 for 300s, User2: raw=2 for 300s (day1 part)
        # Accumulated slots: 2 + 2 = 4
        pd1 = result.project_usage_deltas[project_day1_key]
        assert pd1.slots["cpu"] == Decimal("4")
        assert pd1.duration_seconds == 600  # 300 + 300

        project_day2_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            period_date=date(2024, 1, 16),
        )
        # User2 only: raw=2 for 300s (day2 part)
        pd2 = result.project_usage_deltas[project_day2_key]
        assert pd2.slots["cpu"] == Decimal("2")
        assert pd2.duration_seconds == 300


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
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 55, 0),
            period_end=make_datetime(2024, 1, 16, 0, 0, 0),  # Exactly midnight
            resource_usage=ResourceSlot({"cpu": Decimal("600")}),
            occupied_slots=raw_slots,
            user_uuid=user_uuid,
            project_id=project_id,
        )

        result = aggregator.aggregate_kernel_usage_to_buckets([spec])

        # Should be entirely in Day 1 (end is exclusive boundary)
        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        assert user_key.period_date == date(2024, 1, 15)
        delta = result.user_usage_deltas[user_key]
        assert delta.slots["cpu"] == Decimal("2")
        assert delta.duration_seconds == 300

    def test_spec_starting_exactly_at_midnight(self, aggregator: FairShareAggregator) -> None:
        """Spec starting exactly at midnight is in the new day."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cpu": Decimal("2")})

        spec = make_spec(
            period_start=make_datetime(2024, 1, 16, 0, 0, 0),  # Exactly midnight
            period_end=make_datetime(2024, 1, 16, 0, 5, 0),
            resource_usage=ResourceSlot({"cpu": Decimal("600")}),
            occupied_slots=raw_slots,
            user_uuid=user_uuid,
            project_id=project_id,
        )

        result = aggregator.aggregate_kernel_usage_to_buckets([spec])

        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        assert user_key.period_date == date(2024, 1, 16)

    def test_multiple_resource_types(self, aggregator: FairShareAggregator) -> None:
        """Multiple resource types are all split by day with correct durations."""
        raw_slots = ResourceSlot({
            "cpu": Decimal("2"),
            "mem": Decimal("4096"),
            "cuda.shares": Decimal("1"),
        })
        spec = make_spec(
            period_start=make_datetime(2024, 1, 15, 23, 58, 0),
            period_end=make_datetime(2024, 1, 16, 0, 2, 0),  # 4 minutes, 50/50 split
            resource_usage=ResourceSlot({
                "cpu": Decimal("480"),
                "mem": Decimal("8192"),
                "cuda.shares": Decimal("200"),
            }),
            occupied_slots=raw_slots,
        )

        result = aggregator.aggregate_kernel_usage_to_buckets([spec])

        assert len(result.user_usage_deltas) == 2

        for _key, delta in result.user_usage_deltas.items():
            # Each day gets raw slots + 120 seconds
            assert delta.slots["cpu"] == Decimal("2")
            assert delta.slots["mem"] == Decimal("4096")
            assert delta.slots["cuda.shares"] == Decimal("1")
            assert delta.duration_seconds == 120
