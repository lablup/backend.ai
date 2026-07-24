from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest

from ai.backend.agent.stats import MovingStatistics, StatContext
from ai.backend.common.types import PID, ContainerId


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


class _FakeDocker:
    """
    Minimal aiodocker.Docker stand-in for ``StatContext._get_processes``.

    ``responses`` maps a container id to either the ``Processes`` payload rows
    or the literal string ``"hang"`` to simulate a container whose docker "top"
    query never returns (e.g. a container stuck in D-state).
    """

    def __init__(self, responses: dict[str, Any]) -> None:
        self._responses = responses

    async def _query_json(self, path: str, method: str = "GET") -> dict[str, Any]:
        # path looks like "containers/{container_id}/top"
        container_id = path.split("/")[1]
        resp = self._responses[container_id]
        if resp == "hang":
            await asyncio.Event().wait()  # never resolves
        return {"Processes": resp}


class TestGetProcessesTimeout:
    """A single unresponsive container must not stall PID discovery for others."""

    @pytest.fixture
    def stat_ctx(self) -> StatContext:
        # _get_processes does not touch instance state, so bypass __init__
        # (which requires a full agent + config) and exercise the method directly.
        return StatContext.__new__(StatContext)

    async def test_returns_pids_for_healthy_container(self, stat_ctx: StatContext) -> None:
        docker = _FakeDocker({"healthy": [["root", "1234"], ["root", "1235"]]})
        pids = await stat_ctx._get_processes(ContainerId("healthy"), docker, timeout=1.0)  # type: ignore[arg-type]
        assert pids == [PID(1234), PID(1235)]

    async def test_timeout_returns_empty_without_hanging(self, stat_ctx: StatContext) -> None:
        docker = _FakeDocker({"stuck": "hang"})
        # Outer guard: if the per-call timeout were not honored, this would hang
        # and the outer timeout would raise instead of returning [].
        async with asyncio.timeout(5.0):
            pids = await stat_ctx._get_processes(ContainerId("stuck"), docker, timeout=0.1)  # type: ignore[arg-type]
        assert pids == []

    async def test_stuck_container_does_not_block_healthy_ones(self, stat_ctx: StatContext) -> None:
        docker = _FakeDocker({"stuck": "hang", "healthy": [["root", "42"]]})
        # Mirror production: containers are queried concurrently. The stuck one
        # must be skipped while the healthy one is still collected.
        async with asyncio.timeout(5.0):
            results = await asyncio.gather(
                stat_ctx._get_processes(ContainerId("stuck"), docker, timeout=0.1),  # type: ignore[arg-type]
                stat_ctx._get_processes(ContainerId("healthy"), docker, timeout=0.1),  # type: ignore[arg-type]
            )
        assert results[0] == []
        assert results[1] == [PID(42)]
