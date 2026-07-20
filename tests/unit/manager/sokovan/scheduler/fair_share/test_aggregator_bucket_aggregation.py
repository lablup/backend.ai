"""Tests for FairShareAggregator bucket aggregation logic.

Verifies that kernel usage specs are correctly split by day boundaries
and aggregated into user/project/domain buckets.

Each bucket delta is the resource-seconds to add, summed per slice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainUsageBucketKey,
    ProjectUsageBucketKey,
    UserUsageBucketKey,
)
from ai.backend.manager.repositories.resource_usage_history import (
    KernelUsageRecordCreatorSpec,
)
from ai.backend.manager.sokovan.scheduler.fair_share.aggregator import (
    FairShareAggregator,
)

RESOURCE_GROUP_ID = ResourceGroupID(uuid4())

_USER_A = UUID("11111111-1111-4111-8111-111111111111")
_USER_B = UUID("22222222-2222-4222-8222-222222222222")
_USER_C = UUID("33333333-3333-4333-8333-333333333333")
_PROJECT_1 = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_PROJECT_2 = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
_TICK_DAY = date(2026, 7, 17)


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
        resource_group_id=RESOURCE_GROUP_ID,
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

    Each delta is ``sum(amount * duration)`` over the slices in that bucket.
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
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 15),
        )
        assert user_key in result.user_usage_deltas
        delta = result.user_usage_deltas[user_key]
        # 2 CPU for 300s -> 600 CPU-seconds
        assert delta["cpu"] == Decimal("600")

        # Project bucket
        assert len(result.project_usage_deltas) == 1
        project_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="test-domain",
            resource_group="test-rg",
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 15),
        )
        assert project_key in result.project_usage_deltas
        assert result.project_usage_deltas[project_key]["cpu"] == Decimal("600")

        # Domain bucket
        assert len(result.domain_usage_deltas) == 1
        domain_key = DomainUsageBucketKey(
            domain_name="test-domain",
            resource_group="test-rg",
            resource_group_id=specs[0].resource_group_id,
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

        assert len(result.user_usage_deltas) == 1
        user_key = list(result.user_usage_deltas.keys())[0]
        delta = result.user_usage_deltas[user_key]
        # Per slice: 2*300 + 2*300 = 1200, not (2+2) * (300+300) = 2400
        assert delta["cpu"] == Decimal("1200")
        # Durations accumulate: 300 + 300 = 600

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
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 15),
        )
        day2_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 16),
        )

        assert day1_key in result.user_usage_deltas
        assert day2_key in result.user_usage_deltas
        # Day 1: 2 CPU for 180s -> 360 CPU-seconds
        assert result.user_usage_deltas[day1_key]["cpu"] == Decimal("360")
        # Day 2: 2 CPU for 180s -> 360 CPU-seconds
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
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 15),
        )
        day2_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 16),
        )

        # 5 specs at 2 CPU, durations 240 + 300*4 = 1440s
        d1 = result.user_usage_deltas[day1_key]
        assert d1["cpu"] == Decimal("2880")

        # 3 specs at 2 CPU, durations 300 + 300 + 180 = 780s
        d2 = result.user_usage_deltas[day2_key]
        assert d2["cpu"] == Decimal("1560")

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
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 15),
        )
        day2_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 16),
        )

        # 4 complete specs + the crossing spec's day1 part, all at 2 CPU: 1440s
        d1 = result.user_usage_deltas[day1_key]
        assert d1["cpu"] == Decimal("2880")

        # The crossing spec's day2 part + 2 specs, all at 2 CPU: 780s
        d2 = result.user_usage_deltas[day2_key]
        assert d2["cpu"] == Decimal("1560")

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
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 15),
        )
        # User1 and User2 each 2 CPU for 300s: 2*300 + 2*300 = 1200
        pd1 = result.project_usage_deltas[project_day1_key]
        assert pd1["cpu"] == Decimal("1200")  # 300 + 300

        project_day2_key = ProjectUsageBucketKey(
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            resource_group_id=specs[0].resource_group_id,
            period_date=date(2024, 1, 16),
        )
        # User2 only: 2 CPU for 300s (day2 part) -> 600 CPU-seconds
        pd2 = result.project_usage_deltas[project_day2_key]
        assert pd2["cpu"] == Decimal("600")


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
        assert delta["cpu"] == Decimal("600")

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
            assert delta["cpu"] == Decimal("240")
            assert delta["mem"] == Decimal("491520")
            assert delta["cuda.shares"] == Decimal("120")


@dataclass(frozen=True)
class _ConcurrentKernelsCase:
    """One tick observing ``kernel_count`` kernels of the same user."""

    kernel_count: int
    expected_resource_usage: Decimal


class TestConcurrentKernelsNotCrossMultiplied:
    """Regression: a bucket must not scale with the square of the kernel count.

    Summing amounts and durations separately and multiplying afterwards
    inflates a bucket by exactly the number of kernels folded into it.
    """

    @pytest.mark.parametrize(
        "case",
        [
            _ConcurrentKernelsCase(
                kernel_count=1,
                expected_resource_usage=Decimal("300"),
            ),
            _ConcurrentKernelsCase(
                kernel_count=2,
                expected_resource_usage=Decimal("600"),
            ),
            _ConcurrentKernelsCase(
                kernel_count=4,
                expected_resource_usage=Decimal("1200"),
            ),
            _ConcurrentKernelsCase(
                kernel_count=10,
                expected_resource_usage=Decimal("3000"),
            ),
        ],
        ids=lambda case: f"{case.kernel_count}-kernels",
    )
    def test_one_tick_of_concurrent_kernels(
        self,
        aggregator: FairShareAggregator,
        case: _ConcurrentKernelsCase,
    ) -> None:
        """N kernels at 1 fGPU for one 300s slice total N*300 fGPU-seconds."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cuda.shares": Decimal("1")})

        specs = [
            make_spec(
                period_start=make_datetime(2026, 7, 17, 10, 0, 0),
                period_end=make_datetime(2026, 7, 17, 10, 5, 0),
                resource_usage=ResourceSlot({"cuda.shares": Decimal("300")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            )
            for _ in range(case.kernel_count)
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        user_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            resource_group_id=RESOURCE_GROUP_ID,
            period_date=date(2026, 7, 17),
        )
        delta = result.user_usage_deltas[user_key]
        assert delta["cuda.shares"] == case.expected_resource_usage

        domain_key = DomainUsageBucketKey(
            domain_name="default",
            resource_group="default",
            resource_group_id=RESOURCE_GROUP_ID,
            period_date=date(2026, 7, 17),
        )
        domain_delta = result.domain_usage_deltas[domain_key]
        assert domain_delta["cuda.shares"] == case.expected_resource_usage

    def test_full_day_of_four_kernels(self, aggregator: FairShareAggregator) -> None:
        """A full day of 4 kernels sums to 4 * 86400, not 4 * 4 * 86400."""
        user_uuid = uuid4()
        project_id = uuid4()
        raw_slots = ResourceSlot({"cuda.shares": Decimal("1")})

        specs = [
            make_spec(
                period_start=datetime(2026, 7, 17, tzinfo=UTC).replace(
                    hour=slice_index // 12, minute=(slice_index % 12) * 5
                ),
                period_end=datetime(2026, 7, 17, tzinfo=UTC).replace(
                    hour=slice_index // 12, minute=(slice_index % 12) * 5
                )
                + timedelta(seconds=300),
                resource_usage=ResourceSlot({"cuda.shares": Decimal("300")}),
                occupied_slots=raw_slots,
                user_uuid=user_uuid,
                project_id=project_id,
            )
            for slice_index in range(288)
            for _ in range(4)
        ]

        result = aggregator.aggregate_kernel_usage_to_buckets(specs)

        user_key = UserUsageBucketKey(
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name="default",
            resource_group="default",
            resource_group_id=RESOURCE_GROUP_ID,
            period_date=date(2026, 7, 17),
        )
        delta = result.user_usage_deltas[user_key]
        assert delta["cuda.shares"] == Decimal("345600")


@dataclass(frozen=True)
class _Workload:
    """Identical kernels one user runs inside one project."""

    user_uuid: UUID
    project_id: UUID
    shares: Decimal
    kernel_count: int


@dataclass(frozen=True)
class _UserBucketExpectation:
    label: str
    user_uuid: UUID
    project_id: UUID
    resource_usage: Decimal


@dataclass(frozen=True)
class _ProjectBucketExpectation:
    label: str
    project_id: UUID
    resource_usage: Decimal


class TestMultiTenantTick:
    """One observation tick spanning two projects, three users and seven kernels.

    The inflation compounds up the hierarchy, since each level multiplies by
    the kernel count *it* aggregates: 2x for a user here, 3x for a project,
    7x for the domain.  User A runs in both projects, so user buckets must
    stay keyed by (user, project).
    """

    @pytest.fixture
    def multi_tenant_specs(self) -> list[KernelUsageRecordCreatorSpec]:
        """One 5-minute slice per kernel, all on the same day."""
        workloads = [
            _Workload(_USER_A, _PROJECT_1, Decimal("1"), 2),
            _Workload(_USER_B, _PROJECT_1, Decimal("2"), 1),
            _Workload(_USER_A, _PROJECT_2, Decimal("1"), 3),
            _Workload(_USER_C, _PROJECT_2, Decimal("4"), 1),
        ]
        return [
            make_spec(
                period_start=make_datetime(2026, 7, 17, 10, 0, 0),
                period_end=make_datetime(2026, 7, 17, 10, 5, 0),
                resource_usage=ResourceSlot({"cuda.shares": workload.shares * 300}),
                occupied_slots=ResourceSlot({"cuda.shares": workload.shares}),
                user_uuid=workload.user_uuid,
                project_id=workload.project_id,
            )
            for workload in workloads
            for _ in range(workload.kernel_count)
        ]

    @pytest.mark.parametrize(
        "case",
        [
            _UserBucketExpectation(
                label="user-a-project-1",  # 2 kernels * 1 share * 300s
                user_uuid=_USER_A,
                project_id=_PROJECT_1,
                resource_usage=Decimal("600"),
            ),
            _UserBucketExpectation(
                label="user-b-project-1",  # 1 kernel * 2 shares * 300s
                user_uuid=_USER_B,
                project_id=_PROJECT_1,
                resource_usage=Decimal("600"),
            ),
            _UserBucketExpectation(
                label="user-a-project-2",  # 3 kernels * 1 share * 300s
                user_uuid=_USER_A,
                project_id=_PROJECT_2,
                resource_usage=Decimal("900"),
            ),
            _UserBucketExpectation(
                label="user-c-project-2",  # 1 kernel * 4 shares * 300s
                user_uuid=_USER_C,
                project_id=_PROJECT_2,
                resource_usage=Decimal("1200"),
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_user_buckets_are_keyed_by_user_and_project(
        self,
        aggregator: FairShareAggregator,
        multi_tenant_specs: list[KernelUsageRecordCreatorSpec],
        case: _UserBucketExpectation,
    ) -> None:
        result = aggregator.aggregate_kernel_usage_to_buckets(multi_tenant_specs)

        assert len(result.user_usage_deltas) == 4
        delta = result.user_usage_deltas[
            UserUsageBucketKey(
                user_uuid=case.user_uuid,
                project_id=case.project_id,
                domain_name="default",
                resource_group="default",
                resource_group_id=RESOURCE_GROUP_ID,
                period_date=_TICK_DAY,
            )
        ]
        assert delta["cuda.shares"] == case.resource_usage

    @pytest.mark.parametrize(
        "case",
        [
            _ProjectBucketExpectation(
                label="project-1",  # user A 600 + user B 600
                project_id=_PROJECT_1,
                resource_usage=Decimal("1200"),
            ),
            _ProjectBucketExpectation(
                label="project-2",  # user A 900 + user C 1200
                project_id=_PROJECT_2,
                resource_usage=Decimal("2100"),
            ),
        ],
        ids=lambda case: case.label,
    )
    def test_project_buckets_sum_their_users(
        self,
        aggregator: FairShareAggregator,
        multi_tenant_specs: list[KernelUsageRecordCreatorSpec],
        case: _ProjectBucketExpectation,
    ) -> None:
        result = aggregator.aggregate_kernel_usage_to_buckets(multi_tenant_specs)

        assert len(result.project_usage_deltas) == 2
        delta = result.project_usage_deltas[
            ProjectUsageBucketKey(
                project_id=case.project_id,
                domain_name="default",
                resource_group="default",
                resource_group_id=RESOURCE_GROUP_ID,
                period_date=_TICK_DAY,
            )
        ]
        assert delta["cuda.shares"] == case.resource_usage

    def test_domain_bucket_sums_every_project(
        self,
        aggregator: FairShareAggregator,
        multi_tenant_specs: list[KernelUsageRecordCreatorSpec],
    ) -> None:
        """Project 1 (1200) + project 2 (2100)."""
        result = aggregator.aggregate_kernel_usage_to_buckets(multi_tenant_specs)

        assert len(result.domain_usage_deltas) == 1
        delta = result.domain_usage_deltas[
            DomainUsageBucketKey(
                domain_name="default",
                resource_group="default",
                resource_group_id=RESOURCE_GROUP_ID,
                period_date=_TICK_DAY,
            )
        ]
        assert delta["cuda.shares"] == Decimal("3300")
