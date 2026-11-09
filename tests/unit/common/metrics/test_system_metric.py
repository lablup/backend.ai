from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from prometheus_client import REGISTRY, values
from prometheus_client.parser import text_string_to_metric_families

from ai.backend.common.metrics.metric import CommonMetricRegistry, SystemMetricObserver
from ai.backend.common.metrics.multiprocess import generate_latest_multiprocess

_WORKER_PIDS = ("101", "102", "103")

# MultiProcessValue is untyped; go through Any to avoid [no-untyped-call].
_multiprocess_value_cls: Any = values.MultiProcessValue


@pytest.fixture
def multiprocess_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
async def workers_observed(multiprocess_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Each fake worker writes its system metrics to its own multiprocess file."""
    monkeypatch.setattr(REGISTRY, "register", lambda _collector: None)
    for pid in _WORKER_PIDS:
        monkeypatch.setattr(values, "ValueClass", _multiprocess_value_cls(lambda pid=pid: pid))
        SystemMetricObserver().observe()
    return multiprocess_dir


def _collect_samples(metric_name: str) -> list[tuple[dict[str, str], float]]:
    exposition = generate_latest_multiprocess().decode("utf-8")
    return [
        (sample.labels, sample.value)
        for family in text_string_to_metric_families(exposition)
        if family.name == metric_name
        for sample in family.samples
    ]


class TestSystemMetricObserver:
    @pytest.mark.parametrize(
        "metric_name", ["backendai_async_task_count", "backendai_memory_used_rss"]
    )
    async def test_one_series_per_worker(self, workers_observed: Path, metric_name: str) -> None:
        samples = _collect_samples(metric_name)

        assert sorted(labels["pid"] for labels, _ in samples) == sorted(_WORKER_PIDS)
        assert all(value > 0 for _, value in samples)


class TestCommonMetricRegistry:
    async def test_to_prometheus_runs_off_the_event_loop(self, multiprocess_dir: Path) -> None:
        registry = CommonMetricRegistry.instance()

        output = await asyncio.to_thread(registry.to_prometheus)

        assert isinstance(output, str)
