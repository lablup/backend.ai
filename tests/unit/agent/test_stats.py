from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.agent.agent import AbstractAgent
from ai.backend.agent.stats import MovingStatistics, StatContext


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


class TestStatContextLockIndependence:
    """Verify per-scope locks do not block each other."""

    @pytest.mark.asyncio
    async def test_different_scopes_do_not_block_each_other(self) -> None:
        mock_agent = AsyncMock(spec=AbstractAgent)
        ctx = StatContext(mock_agent)

        # If locks were shared, acquiring _container_lock / _process_lock
        # while _node_lock is held would deadlock and hit the timeout.
        async with ctx._node_lock:
            async with asyncio.timeout(1.0):
                async with ctx._container_lock:
                    async with ctx._process_lock:
                        pass  # all three locks held concurrently = independent
