from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import patch

import pytest

from ai.backend.agent.stats import MovingStatistics


class TestMovingStatistics:
    """Tests for MovingStatistics class, focusing on counter reset detection."""

    @pytest.fixture
    def stats(self) -> MovingStatistics:
        return MovingStatistics()

    @dataclass(frozen=True)
    class DiffTestCase:
        id: str
        first_value: Decimal
        second_value: Decimal
        expected_diff: Decimal

    @pytest.mark.parametrize(
        "case",
        [
            DiffTestCase(
                id="positive_delta_for_increasing_values",
                first_value=Decimal(100),
                second_value=Decimal(150),
                expected_diff=Decimal(50),
            ),
            DiffTestCase(
                id="zero_on_counter_reset",
                first_value=Decimal(1000),
                second_value=Decimal(100),
                expected_diff=Decimal(0),
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_diff(self, stats: MovingStatistics, case: DiffTestCase) -> None:
        """Test that diff correctly handles both increasing values and counter resets."""
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(case.first_value)
            stats.update(case.second_value)

        assert stats.diff == case.expected_diff

    @dataclass(frozen=True)
    class RateTestCase:
        id: str
        first_value: Decimal
        second_value: Decimal
        time_values: tuple[float, float]
        expected_rate: Decimal

    @pytest.mark.parametrize(
        "case",
        [
            RateTestCase(
                id="positive_rate_for_increasing_values",
                first_value=Decimal(100),
                second_value=Decimal(200),
                time_values=(1.0, 3.0),
                expected_rate=Decimal(50),
            ),
            RateTestCase(
                id="zero_on_counter_reset",
                first_value=Decimal(500),
                second_value=Decimal(50),
                time_values=(1.0, 2.0),
                expected_rate=Decimal(0),
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_rate(self, stats: MovingStatistics, case: RateTestCase) -> None:
        """Test that rate correctly handles both increasing values and counter resets."""
        with patch("time.perf_counter", side_effect=list(case.time_values)):
            stats.update(case.first_value)
            stats.update(case.second_value)

        assert stats.rate == case.expected_rate


class TestMovingStatisticsRateCeiling:
    """Tests for rate_ceiling outlier detection in MovingStatistics."""

    def test_rate_within_ceiling_is_returned(self) -> None:
        """Rate below ceiling should be returned as-is."""
        stats = MovingStatistics(rate_ceiling=Decimal(1000))
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(100))
            stats.update(Decimal(600))

        assert stats.rate == Decimal(500)

    def test_rate_exceeding_ceiling_clamped_to_zero(self) -> None:
        """Rate exceeding ceiling should be clamped to zero (likely erroneous reading)."""
        stats = MovingStatistics(rate_ceiling=Decimal(1000))
        # Simulate a namespace confusion spike: counter jumps from container-level
        # value (100) to host-level value (1_000_000) in 1 second = rate 999_900
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(100))
            stats.update(Decimal(1_000_000))

        assert stats.rate == Decimal(0)

    def test_rate_without_ceiling_is_unlimited(self) -> None:
        """Without rate_ceiling, arbitrarily large rates should be returned."""
        stats = MovingStatistics()
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(100))
            stats.update(Decimal(1_000_000))

        assert stats.rate == Decimal(999_900)

    def test_rate_ceiling_does_not_affect_counter_reset(self) -> None:
        """Counter reset (negative delta) should still return zero regardless of ceiling."""
        stats = MovingStatistics(rate_ceiling=Decimal(1000))
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(500))
            stats.update(Decimal(50))

        assert stats.rate == Decimal(0)
