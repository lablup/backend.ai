from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import patch

import pytest

from ai.backend.agent.stats import Measurement, Metric, MetricTypes, MovingStatistics


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


# Large enough that leaking it into `current` reads as an unmistakable spike
# (pct would be 1,000,000%), never as a plausible utilization value.
_HUGE_CPU_USED_MSEC = Decimal(10_000_000)


class TestMetric:
    """Tests for Metric class, focusing on current_hook application."""

    @dataclass(frozen=True)
    class CreationTestCase:
        id: str
        initial_value: Decimal
        current_hook: Callable[[Metric], Decimal] | None
        expected_current: Decimal
        expected_pct: str

    @pytest.mark.parametrize(
        "case",
        [
            CreationTestCase(
                id="rate_hook_applied_to_first_observation",
                initial_value=_HUGE_CPU_USED_MSEC,
                current_hook=lambda metric: metric.stats.rate,
                expected_current=Decimal(0),
                expected_pct="0",
            ),
            CreationTestCase(
                id="no_hook_keeps_raw_value",
                initial_value=_HUGE_CPU_USED_MSEC,
                current_hook=None,
                expected_current=_HUGE_CPU_USED_MSEC,
                expected_pct="1000000",
            ),
        ],
        ids=lambda case: case.id,
    )
    def test_creation_applies_current_hook(self, case: CreationTestCase) -> None:
        """Test that a hook-derived metric does not expose the raw cumulative counter
        as current/pct on the first observation."""
        metric = Metric(
            key="cpu_util",
            type=MetricTypes.UTILIZATION,
            unit_hint="percent",
            stats=MovingStatistics(case.initial_value),
            stats_filter=frozenset({"avg", "max"}),
            current=case.initial_value,
            capacity=Decimal(1000),
            current_hook=case.current_hook,
        )

        assert metric.current == case.expected_current
        assert metric.to_serializable_dict()["pct"] == case.expected_pct

    @pytest.fixture
    def cpu_util_metric(self) -> Metric:
        with patch("time.perf_counter", return_value=1.0):
            return Metric(
                key="cpu_util",
                type=MetricTypes.UTILIZATION,
                unit_hint="percent",
                stats=MovingStatistics(Decimal(1000)),
                stats_filter=frozenset({"avg", "max"}),
                current=Decimal(1000),
                capacity=Decimal(1000),
                current_hook=lambda metric: metric.stats.rate,
            )

    def test_update_applies_current_hook(self, cpu_util_metric: Metric) -> None:
        """Test that subsequent observations report the rate derived from the counter delta."""
        with patch("time.perf_counter", return_value=2.0):
            cpu_util_metric.update(Measurement(Decimal(1500)))

        assert cpu_util_metric.current == Decimal(500)
        assert cpu_util_metric.to_serializable_dict()["pct"] == "50"
