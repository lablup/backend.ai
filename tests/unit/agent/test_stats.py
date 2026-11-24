from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiodocker
import pytest

from ai.backend.agent.stats import (
    Measurement,
    Metric,
    MetricTypes,
    MovingStatistics,
    StatContext,
    StatModes,
)
from ai.backend.common.types import PID, ContainerId, KernelId, MetricKey


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
            unit_hint="millicores",
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
                unit_hint="millicores",
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


class TestGetProcesses:
    """Tests for StatContext._get_processes, which reads a container's PIDs from Docker."""

    @pytest.fixture
    def stat_ctx(self) -> StatContext:
        return StatContext(MagicMock(), MagicMock(), mode=StatModes.DOCKER)

    def _docker_answering(self, top: dict[str, Any]) -> aiodocker.Docker:
        docker = MagicMock(spec=aiodocker.Docker)
        docker._query_json = AsyncMock(return_value=top)
        return docker

    async def test_returns_the_pids_docker_lists(self, stat_ctx: StatContext) -> None:
        docker = self._docker_answering({
            "Titles": ["UID", "PID", "CMD"],
            "Processes": [["root", "1", "/sbin/docker-init"], ["work", "42", "python"]],
        })

        pids = await stat_ctx._get_processes(ContainerId("c1"), docker)

        assert pids == [PID(1), PID(42)]

    async def test_a_null_process_list_is_unknown(self, stat_ctx: StatContext) -> None:
        """Docker answers `"Processes": null` for a running container it cannot list."""
        docker = self._docker_answering({"Titles": ["UID", "PID", "CMD"], "Processes": None})

        pids = await stat_ctx._get_processes(ContainerId("c1"), docker)

        assert pids is None


class TestCollectPerContainerProcessStat:
    """The pruning of per-process metrics after a collection pass."""

    @pytest.fixture
    def container_id(self) -> ContainerId:
        return ContainerId("c1")

    @pytest.fixture
    def lazy_remove(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def stat_ctx(self, container_id: ContainerId, lazy_remove: AsyncMock) -> StatContext:
        kernel = MagicMock()
        kernel.__getitem__.side_effect = {"container_id": container_id}.__getitem__
        agent = MagicMock()
        agent.kernel_registry = {KernelId(uuid.uuid4()): kernel}
        agent.computers = {}
        ctx = StatContext(agent, MagicMock(), mode=StatModes.DOCKER)
        ctx.process_metrics = {container_id: {PID(42): {MetricKey("cpu_util"): MagicMock()}}}
        ctx._utilization_metric_observer = MagicMock()
        ctx._utilization_metric_observer.lazy_remove_process_metric = lazy_remove
        return ctx

    async def _collect_with_top(
        self, stat_ctx: StatContext, container_id: ContainerId, top: dict[str, Any]
    ) -> None:
        docker = MagicMock()
        docker._query_json = AsyncMock(return_value=top)
        docker_cm = MagicMock()
        docker_cm.__aenter__ = AsyncMock(return_value=docker)
        docker_cm.__aexit__ = AsyncMock(return_value=None)
        with (
            patch("ai.backend.agent.stats.sys.platform", "linux"),
            patch("ai.backend.agent.stats.aiodocker.Docker", return_value=docker_cm),
        ):
            await stat_ctx.collect_per_container_process_stat([container_id])

    async def test_keeps_the_metrics_of_a_container_whose_list_is_null(
        self, stat_ctx: StatContext, container_id: ContainerId, lazy_remove: AsyncMock
    ) -> None:
        await self._collect_with_top(stat_ctx, container_id, {"Processes": None})

        lazy_remove.assert_not_called()

    async def test_prunes_the_metrics_of_a_pid_no_longer_listed(
        self, stat_ctx: StatContext, container_id: ContainerId, lazy_remove: AsyncMock
    ) -> None:
        await self._collect_with_top(stat_ctx, container_id, {"Processes": []})

        lazy_remove.assert_awaited_once()
