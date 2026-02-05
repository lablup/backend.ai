"""Unit tests for common calculation utilities in usage bucket metrics."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.api.gql.fair_share.types import ResourceSlotGQL
from ai.backend.manager.api.gql.resource_usage.types.common_calculations import (
    calculate_average_capacity_per_second,
    calculate_average_daily_usage,
    calculate_usage_capacity_ratio,
)


class TestCalculateAverageDailyUsage:
    """Tests for calculate_average_daily_usage function."""

    @pytest.fixture
    def one_day_period(self) -> tuple[date, date]:
        """One day period (2026-02-01 to 2026-02-02)."""
        return (date(2026, 2, 1), date(2026, 2, 2))

    @pytest.fixture
    def multi_day_period(self) -> tuple[date, date]:
        """Seven day period (2026-02-01 to 2026-02-08)."""
        return (date(2026, 2, 1), date(2026, 2, 8))

    @pytest.fixture
    def zero_day_period(self) -> tuple[date, date]:
        """Zero day period (same start and end date)."""
        return (date(2026, 2, 1), date(2026, 2, 1))

    @pytest.fixture
    def sample_resource_usage(self) -> ResourceSlotGQL:
        """Sample resource usage with cpu and mem for single day."""
        slot = ResourceSlot({
            "cpu": Decimal("172800.0"),  # 2 cores * 86400 seconds = 172800 core-seconds
            "mem": Decimal("34359738368.0"),  # 32 GiB * 86400 seconds
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def multi_day_resource_usage(self) -> ResourceSlotGQL:
        """Sample resource usage with cpu for 7 days."""
        slot = ResourceSlot({
            "cpu": Decimal("1209600.0"),  # 2 cores * 7 days * 86400 seconds
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def empty_resource_usage(self) -> ResourceSlotGQL:
        """Empty resource usage with no entries."""
        return ResourceSlotGQL(entries=[])

    @pytest.fixture
    def multi_resource_usage(self) -> ResourceSlotGQL:
        """Resource usage with multiple resource types."""
        slot = ResourceSlot({
            "cpu": Decimal("172800.0"),
            "mem": Decimal("34359738368.0"),
            "cuda.shares": Decimal("86400.0"),  # 1 GPU share for 1 day
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    def test_calculates_daily_average_for_single_day(
        self,
        sample_resource_usage: ResourceSlotGQL,
        one_day_period: tuple[date, date],
    ) -> None:
        """Test daily average calculation for 1-day period."""
        # Given
        period_start, period_end = one_day_period

        # When
        result = calculate_average_daily_usage(
            sample_resource_usage,
            period_start,
            period_end,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        assert result_dict["cpu"] == Decimal("172800.0")
        assert result_dict["mem"] == Decimal("34359738368.0")

    def test_calculates_daily_average_for_multiple_days(
        self,
        multi_day_resource_usage: ResourceSlotGQL,
        multi_day_period: tuple[date, date],
    ) -> None:
        """Test daily average calculation for 7-day period."""
        # Given
        period_start, period_end = multi_day_period

        # When
        result = calculate_average_daily_usage(
            multi_day_resource_usage,
            period_start,
            period_end,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        # 1209600 / 7 = 172800
        assert result_dict["cpu"] == Decimal("172800.0")

    def test_returns_empty_for_zero_duration(
        self,
        sample_resource_usage: ResourceSlotGQL,
        zero_day_period: tuple[date, date],
    ) -> None:
        """Test that zero bucket duration returns empty ResourceSlotGQL."""
        # Given
        period_start, period_end = zero_day_period

        # When
        result = calculate_average_daily_usage(
            sample_resource_usage,
            period_start,
            period_end,
        )

        # Then
        assert len(result.entries) == 0

    def test_handles_empty_resource_usage(
        self,
        empty_resource_usage: ResourceSlotGQL,
        one_day_period: tuple[date, date],
    ) -> None:
        """Test handling of empty resource usage."""
        # Given
        period_start, period_end = one_day_period

        # When
        result = calculate_average_daily_usage(
            empty_resource_usage,
            period_start,
            period_end,
        )

        # Then
        assert len(result.entries) == 0

    def test_calculates_for_multiple_resource_types(
        self,
        multi_resource_usage: ResourceSlotGQL,
        one_day_period: tuple[date, date],
    ) -> None:
        """Test calculation for multiple resource types simultaneously."""
        # Given
        period_start, period_end = one_day_period

        # When
        result = calculate_average_daily_usage(
            multi_resource_usage,
            period_start,
            period_end,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        assert len(result_dict) == 3
        assert result_dict["cpu"] == Decimal("172800.0")
        assert result_dict["mem"] == Decimal("34359738368.0")
        assert result_dict["cuda.shares"] == Decimal("86400.0")


class TestCalculateUsageCapacityRatio:
    """Tests for calculate_usage_capacity_ratio function."""

    @pytest.fixture
    def sample_resource_usage(self) -> ResourceSlotGQL:
        """Sample resource usage with cpu."""
        slot = ResourceSlot({
            "cpu": Decimal("172800.0"),  # 2 cores * 86400 seconds
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def sample_capacity(self) -> ResourceSlotGQL:
        """Sample capacity with 8 CPU cores."""
        slot = ResourceSlot({
            "cpu": Decimal("8.0"),
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def zero_capacity(self) -> ResourceSlotGQL:
        """Capacity with zero CPU."""
        slot = ResourceSlot({
            "cpu": Decimal("0.0"),
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def partial_capacity(self) -> ResourceSlotGQL:
        """Capacity with only cpu (no mem)."""
        slot = ResourceSlot({
            "cpu": Decimal("8.0"),
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def multi_resource_usage_and_capacity(
        self,
    ) -> tuple[ResourceSlotGQL, ResourceSlotGQL]:
        """Multiple resource types with usage and capacity."""
        usage_slot = ResourceSlot({
            "cpu": Decimal("172800.0"),
            "mem": Decimal("34359738368.0"),
            "cuda.shares": Decimal("43200.0"),  # 0.5 GPU share for 1 day
        })
        capacity_slot = ResourceSlot({
            "cpu": Decimal("8.0"),
            "mem": Decimal("68719476736.0"),  # 64 GiB
            "cuda.shares": Decimal("4.0"),
        })
        return (
            ResourceSlotGQL.from_resource_slot(usage_slot),
            ResourceSlotGQL.from_resource_slot(capacity_slot),
        )

    @pytest.fixture
    def usage_with_mem(self) -> ResourceSlotGQL:
        """Resource usage including memory."""
        slot = ResourceSlot({
            "cpu": Decimal("172800.0"),
            "mem": Decimal("1000.0"),
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def high_usage(self) -> ResourceSlotGQL:
        """High resource usage exceeding capacity."""
        slot = ResourceSlot({
            "cpu": Decimal("864000.0"),  # 10 cores * 86400 seconds
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    def test_calculates_ratio_normal_case(
        self,
        sample_resource_usage: ResourceSlotGQL,
        sample_capacity: ResourceSlotGQL,
    ) -> None:
        """Test ratio calculation for normal case."""
        # Given

        # When
        result = calculate_usage_capacity_ratio(
            sample_resource_usage,
            sample_capacity,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        # 172800 / 8 = 21600 seconds (6 hours)
        assert result_dict["cpu"] == Decimal("21600.0")

    def test_skips_zero_capacity_resources(
        self,
        sample_resource_usage: ResourceSlotGQL,
        zero_capacity: ResourceSlotGQL,
    ) -> None:
        """Test that resources with zero capacity are excluded from result."""
        # Given

        # When
        result = calculate_usage_capacity_ratio(
            sample_resource_usage,
            zero_capacity,
        )

        # Then
        # cpu should be excluded because capacity is zero
        assert len(result.entries) == 0

    def test_handles_missing_capacity_for_resource(
        self,
        usage_with_mem: ResourceSlotGQL,
        partial_capacity: ResourceSlotGQL,
    ) -> None:
        """Test handling when capacity info is missing for a resource type."""
        # Given

        # When
        result = calculate_usage_capacity_ratio(
            usage_with_mem,
            partial_capacity,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        # cpu should be calculated, mem should be excluded
        assert "cpu" in result_dict
        assert "mem" not in result_dict

    def test_handles_usage_exceeding_capacity(
        self,
        high_usage: ResourceSlotGQL,
        sample_capacity: ResourceSlotGQL,
    ) -> None:
        """Test handling when usage exceeds available capacity."""
        # Given

        # When
        result = calculate_usage_capacity_ratio(
            high_usage,
            sample_capacity,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        # 864000 / 8 = 108000 seconds (>86400, more than 1 day)
        assert result_dict["cpu"] == Decimal("108000.0")
        assert result_dict["cpu"] > Decimal("86400.0")

    def test_calculates_for_multiple_resources(
        self,
        multi_resource_usage_and_capacity: tuple[ResourceSlotGQL, ResourceSlotGQL],
    ) -> None:
        """Test calculation for multiple resource types simultaneously."""
        # Given
        usage, capacity = multi_resource_usage_and_capacity

        # When
        result = calculate_usage_capacity_ratio(usage, capacity)

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        assert len(result_dict) == 3
        # cpu: 172800 / 8 = 21600
        assert result_dict["cpu"] == Decimal("21600.0")
        # mem: 34359738368 / 68719476736 = 0.5
        assert result_dict["mem"] == Decimal("0.5")
        # cuda.shares: 43200 / 4 = 10800
        assert result_dict["cuda.shares"] == Decimal("10800.0")


class TestCalculateAverageCapacityPerSecond:
    """Tests for calculate_average_capacity_per_second function."""

    @pytest.fixture
    def one_day_period(self) -> tuple[date, date]:
        """One day period (2026-02-01 to 2026-02-02)."""
        return (date(2026, 2, 1), date(2026, 2, 2))

    @pytest.fixture
    def multi_day_period(self) -> tuple[date, date]:
        """Seven day period (2026-02-01 to 2026-02-08)."""
        return (date(2026, 2, 1), date(2026, 2, 8))

    @pytest.fixture
    def zero_day_period(self) -> tuple[date, date]:
        """Zero day period (same start and end date)."""
        return (date(2026, 2, 1), date(2026, 2, 1))

    @pytest.fixture
    def sample_capacity(self) -> ResourceSlotGQL:
        """Sample capacity with 8 CPU cores."""
        slot = ResourceSlot({
            "cpu": Decimal("8.0"),
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    @pytest.fixture
    def empty_capacity(self) -> ResourceSlotGQL:
        """Empty capacity with no entries."""
        return ResourceSlotGQL(entries=[])

    @pytest.fixture
    def multi_resource_capacity(self) -> ResourceSlotGQL:
        """Capacity with multiple resource types."""
        slot = ResourceSlot({
            "cpu": Decimal("8.0"),
            "mem": Decimal("68719476736.0"),  # 64 GiB
            "cuda.shares": Decimal("4.0"),
        })
        return ResourceSlotGQL.from_resource_slot(slot)

    def test_calculates_capacity_per_second_for_single_day(
        self,
        sample_capacity: ResourceSlotGQL,
        one_day_period: tuple[date, date],
    ) -> None:
        """Test capacity per second calculation for 1-day period."""
        # Given
        period_start, period_end = one_day_period

        # When
        result = calculate_average_capacity_per_second(
            sample_capacity,
            period_start,
            period_end,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        # 8.0 / 86400 ≈ 0.0000925925...
        expected = Decimal("8.0") / Decimal("86400")
        assert result_dict["cpu"] == expected

    def test_calculates_capacity_per_second_for_multiple_days(
        self,
        sample_capacity: ResourceSlotGQL,
        multi_day_period: tuple[date, date],
    ) -> None:
        """Test capacity per second calculation for 7-day period."""
        # Given
        period_start, period_end = multi_day_period

        # When
        result = calculate_average_capacity_per_second(
            sample_capacity,
            period_start,
            period_end,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        # 8.0 / (7 * 86400) = 8.0 / 604800 ≈ 0.00001322751...
        expected = Decimal("8.0") / (Decimal("7") * Decimal("86400"))
        assert result_dict["cpu"] == expected

    def test_returns_empty_for_zero_duration(
        self,
        sample_capacity: ResourceSlotGQL,
        zero_day_period: tuple[date, date],
    ) -> None:
        """Test that zero bucket duration returns empty ResourceSlotGQL."""
        # Given
        period_start, period_end = zero_day_period

        # When
        result = calculate_average_capacity_per_second(
            sample_capacity,
            period_start,
            period_end,
        )

        # Then
        assert len(result.entries) == 0

    def test_handles_empty_capacity(
        self,
        empty_capacity: ResourceSlotGQL,
        one_day_period: tuple[date, date],
    ) -> None:
        """Test handling of empty capacity."""
        # Given
        period_start, period_end = one_day_period

        # When
        result = calculate_average_capacity_per_second(
            empty_capacity,
            period_start,
            period_end,
        )

        # Then
        assert len(result.entries) == 0

    def test_calculates_for_multiple_resource_types(
        self,
        multi_resource_capacity: ResourceSlotGQL,
        one_day_period: tuple[date, date],
    ) -> None:
        """Test calculation for multiple resource types simultaneously."""
        # Given
        period_start, period_end = one_day_period

        # When
        result = calculate_average_capacity_per_second(
            multi_resource_capacity,
            period_start,
            period_end,
        )

        # Then
        result_dict = {entry.resource_type: entry.quantity for entry in result.entries}
        assert len(result_dict) == 3
        # cpu: 8.0 / 86400
        assert result_dict["cpu"] == Decimal("8.0") / Decimal("86400")
        # mem: 68719476736 / 86400
        assert result_dict["mem"] == Decimal("68719476736.0") / Decimal("86400")
        # cuda.shares: 4.0 / 86400
        assert result_dict["cuda.shares"] == Decimal("4.0") / Decimal("86400")
