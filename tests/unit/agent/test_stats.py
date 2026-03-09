from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.stats import (
    ContainerMeasurement,
    MetricTypes,
    MovingStatistics,
    StatContext,
)
from ai.backend.common.types import MetricKey


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


def _make_stat_context(computers: dict[str, MagicMock]) -> StatContext:
    """Create a minimal StatContext with mocked agent for testing collect_container_stat."""
    mock_agent = MagicMock()
    mock_agent.kernel_registry = {}
    mock_agent.computers = computers
    ctx = object.__new__(StatContext)
    ctx.agent = mock_agent
    ctx.node_metrics = {}
    ctx.device_metrics = {}
    ctx.kernel_metrics = {}
    ctx.process_metrics = {}
    ctx._timestamps = {}
    ctx._utilization_metric_observer = MagicMock()
    ctx._stage_observer = MagicMock()
    return ctx


def _make_computer(gather_fn: AsyncMock) -> MagicMock:
    """Create a mock ComputerContext whose instance.gather_container_measures calls gather_fn."""
    computer = MagicMock()
    computer.instance.gather_container_measures = gather_fn
    return computer


class TestPluginTimeout:
    """Tests for per-plugin timeout in collect_container_stat()."""

    async def test_hanging_plugin_times_out_while_others_succeed(self) -> None:
        """When one plugin hangs beyond the timeout, it raises TimeoutError
        while other plugins return their results normally."""

        async def _fast_plugin(
            ctx: StatContext, container_ids: Sequence[str]
        ) -> Sequence[ContainerMeasurement]:
            return [
                ContainerMeasurement(
                    key=MetricKey("cpu_util"),
                    type=MetricTypes.UTILIZATION,
                    per_container={},
                )
            ]

        async def _hanging_plugin(
            ctx: StatContext, container_ids: Sequence[str]
        ) -> Sequence[ContainerMeasurement]:
            await asyncio.sleep(3600)  # hang "forever"
            return []

        fast_computer = _make_computer(AsyncMock(side_effect=_fast_plugin))
        slow_computer = _make_computer(AsyncMock(side_effect=_hanging_plugin))
        computers = {"fast_dev": fast_computer, "slow_dev": slow_computer}
        stat_ctx = _make_stat_context(computers)

        with patch("ai.backend.agent.stats._PLUGIN_TIMEOUT", 0.1):
            await stat_ctx.collect_container_stat([])

        # Fast plugin was called and succeeded
        fast_computer.instance.gather_container_measures.assert_called_once()
        # Slow plugin was also called (but timed out)
        slow_computer.instance.gather_container_measures.assert_called_once()

    async def test_all_plugins_complete_within_timeout(self) -> None:
        """When all plugins complete within the timeout, results are collected normally."""
        measurement = ContainerMeasurement(
            key=MetricKey("mem_used"),
            type=MetricTypes.GAUGE,
            per_container={},
        )

        async def _normal_plugin(
            ctx: StatContext, container_ids: Sequence[str]
        ) -> Sequence[ContainerMeasurement]:
            return [measurement]

        computer_a = _make_computer(AsyncMock(side_effect=_normal_plugin))
        computer_b = _make_computer(AsyncMock(side_effect=_normal_plugin))
        computers = {"dev_a": computer_a, "dev_b": computer_b}
        stat_ctx = _make_stat_context(computers)

        with patch("ai.backend.agent.stats._PLUGIN_TIMEOUT", 5.0):
            await stat_ctx.collect_container_stat([])

        # Both plugins were called and completed
        computer_a.instance.gather_container_measures.assert_called_once()
        computer_b.instance.gather_container_measures.assert_called_once()
