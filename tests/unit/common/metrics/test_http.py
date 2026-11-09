from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator

import pytest

from ai.backend.common.metrics.http import PrometheusMetricsGenerator, SystemMetricUpdater


class _BlockingMetric:
    calls: int
    started: threading.Event
    release: threading.Event

    def __init__(self) -> None:
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()

    def to_prometheus(self) -> str:
        self.calls += 1
        self.started.set()
        self.release.wait(timeout=5)
        return f"generation {self.calls}"


class _FailingMetric:
    calls: int

    def __init__(self) -> None:
        self.calls = 0

    def to_prometheus(self) -> str:
        self.calls += 1
        raise RuntimeError("generation failed")


class _CountingObserver:
    calls: int
    fail: bool

    def __init__(self, *, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def observe(self) -> None:
        self.calls += 1
        if self.fail:
            raise RuntimeError("observe failed")


class TestPrometheusMetricsGenerator:
    @pytest.fixture
    def metric(self) -> _BlockingMetric:
        return _BlockingMetric()

    @pytest.fixture
    def generator(self, metric: _BlockingMetric) -> PrometheusMetricsGenerator:
        return PrometheusMetricsGenerator(metric)

    async def test_event_loop_runs_while_generating(
        self, generator: PrometheusMetricsGenerator, metric: _BlockingMetric
    ) -> None:
        scrape = asyncio.create_task(generator.generate())
        await asyncio.to_thread(metric.started.wait, 5)

        other_request = await asyncio.wait_for(asyncio.sleep(0, result="served"), timeout=1)

        assert other_request == "served"
        assert not scrape.done()
        metric.release.set()
        assert await scrape == "generation 1"

    async def test_concurrent_scrapes_share_one_generation(
        self, generator: PrometheusMetricsGenerator, metric: _BlockingMetric
    ) -> None:
        first = asyncio.create_task(generator.generate())
        await asyncio.to_thread(metric.started.wait, 5)
        others = [asyncio.create_task(generator.generate()) for _ in range(3)]
        await asyncio.sleep(0)
        metric.release.set()

        results = await asyncio.gather(first, *others)

        assert results == ["generation 1"] * 4
        assert metric.calls == 1

    async def test_scrape_after_generation_generates_again(
        self, generator: PrometheusMetricsGenerator, metric: _BlockingMetric
    ) -> None:
        metric.release.set()

        assert await generator.generate() == "generation 1"
        assert await generator.generate() == "generation 2"

    async def test_cancelled_scrape_does_not_cancel_shared_generation(
        self, generator: PrometheusMetricsGenerator, metric: _BlockingMetric
    ) -> None:
        cancelled = asyncio.create_task(generator.generate())
        await asyncio.to_thread(metric.started.wait, 5)
        waiting = asyncio.create_task(generator.generate())
        await asyncio.sleep(0)

        cancelled.cancel()
        metric.release.set()

        assert await waiting == "generation 1"
        assert metric.calls == 1

    async def test_failed_generation_is_retried_on_next_scrape(self) -> None:
        metric = _FailingMetric()
        generator = PrometheusMetricsGenerator(metric)

        with pytest.raises(RuntimeError):
            await generator.generate()
        with pytest.raises(RuntimeError):
            await generator.generate()

        assert metric.calls == 2


class TestSystemMetricUpdater:
    @pytest.fixture
    def observer(self) -> _CountingObserver:
        return _CountingObserver()

    @pytest.fixture
    def failing_observer(self) -> _CountingObserver:
        return _CountingObserver(fail=True)

    @pytest.fixture
    async def running_updater(
        self, observer: _CountingObserver
    ) -> AsyncIterator[SystemMetricUpdater]:
        updater = SystemMetricUpdater(observer, interval=0.01)
        updater.start()
        yield updater
        await updater.stop()

    async def test_updates_periodically(
        self, running_updater: SystemMetricUpdater, observer: _CountingObserver
    ) -> None:
        await asyncio.sleep(0.1)

        assert observer.calls >= 3

    async def test_stop_ends_updates(
        self, running_updater: SystemMetricUpdater, observer: _CountingObserver
    ) -> None:
        await asyncio.sleep(0.03)
        await running_updater.stop()
        calls_at_stop = observer.calls

        await asyncio.sleep(0.05)

        assert observer.calls == calls_at_stop

    async def test_failing_observe_keeps_updating(
        self, failing_observer: _CountingObserver
    ) -> None:
        updater = SystemMetricUpdater(failing_observer, interval=0.01)
        updater.start()
        await asyncio.sleep(0.1)
        await updater.stop()

        assert failing_observer.calls >= 3
