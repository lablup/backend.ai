from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from ai.backend.agent.stats import MovingStatistics


class TestMovingStatistics:
    """Tests for MovingStatistics class, focusing on counter reset detection."""

    @pytest.fixture
    def stats(self) -> MovingStatistics:
        return MovingStatistics()

    def test_diff_returns_positive_delta_for_increasing_values(
        self, stats: MovingStatistics
    ) -> None:
        """Test that diff correctly calculates positive delta between consecutive values."""
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(100))
            stats.update(Decimal(150))

        assert stats.diff == Decimal(50)

    def test_diff_returns_zero_on_counter_reset(self, stats: MovingStatistics) -> None:
        """Test that diff returns 0 when counter reset is detected (negative delta)."""
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(1000))
            stats.update(Decimal(100))  # Counter reset: new value < previous value

        assert stats.diff == Decimal(0)

    def test_rate_returns_positive_rate_for_increasing_values(
        self, stats: MovingStatistics
    ) -> None:
        """Test that rate correctly calculates positive rate between consecutive values."""
        with patch("time.perf_counter", side_effect=[1.0, 3.0]):
            stats.update(Decimal(100))
            stats.update(Decimal(200))

        # delta = 100, time_diff = 2.0, rate = 50
        assert stats.rate == Decimal(50)

    def test_rate_returns_zero_on_counter_reset(self, stats: MovingStatistics) -> None:
        """Test that rate returns 0 when counter reset is detected (negative delta)."""
        with patch("time.perf_counter", side_effect=[1.0, 2.0]):
            stats.update(Decimal(500))
            stats.update(Decimal(50))  # Counter reset: new value < previous value

        assert stats.rate == Decimal(0)
