from __future__ import annotations

from decimal import Decimal

import msgpack
from prometheus_client import generate_latest

from ai.backend.kube.controller.stats import (
    ContainerMetrics,
    ContainerSample,
    KernelStats,
    parse_resource_metrics,
)

METRICS = """\
# HELP container_cpu_usage_seconds_total [STABLE] Cumulative cpu time
container_cpu_usage_seconds_total{container="kernel",namespace="ns",pod="s-1-main1"} 2.5 1700000000000
container_cpu_usage_seconds_total{container="krunner",namespace="ns",pod="s-1-main1"} 0.1 1700000000000
container_memory_working_set_bytes{container="kernel",namespace="ns",pod="s-1-main1"} 1048576 1700000000000
node_cpu_usage_seconds_total 100 1700000000000
"""


class TestParseResourceMetrics:
    def test_keeps_only_kernel_containers(self) -> None:
        assert parse_resource_metrics(METRICS) == {
            ("ns", "s-1-main1"): {
                "container_cpu_usage_seconds_total": (Decimal("2.5"), 1700000000000),
                "container_memory_working_set_bytes": (Decimal("1048576"), 1700000000000),
            }
        }


class TestKernelStats:
    def test_cpu_util_is_cpu_time_over_the_sample_interval(self) -> None:
        stats = KernelStats()
        stats.update(ContainerSample(Decimal(1000), Decimal(512), 10_000), Decimal(1024))
        # 15 s of CPU time in 15 s: one core
        stats.update(ContainerSample(Decimal(16000), Decimal(256), 25_000), Decimal(1024))
        packed = msgpack.unpackb(stats.packed())
        assert Decimal(packed["cpu_util"]["current"]) == 1000
        assert Decimal(packed["cpu_util"]["pct"]) == 100
        assert Decimal(packed["mem"]["current"]) == 256
        assert Decimal(packed["mem"]["pct"]) == 25
        assert Decimal(packed["cpu_used"]["current"]) == 16000

    def test_a_repeated_sample_changes_nothing(self) -> None:
        stats = KernelStats()
        sample = ContainerSample(Decimal(1000), Decimal(512), 10_000)
        assert stats.update(sample, Decimal(1024))
        assert not stats.update(sample, Decimal(1024))


class TestContainerMetrics:
    def test_exports_raw_measurements_like_the_agent(self) -> None:
        stats = KernelStats()
        stats.update(ContainerSample(Decimal(16000), Decimal(256), 25_000), Decimal(1024))
        metrics = ContainerMetrics("k8s-local")
        labels = {"backend.ai/session-id": "s", "backend.ai/user-id": "u"}
        metrics.observe(labels, "k1", stats.raw)
        text = generate_latest(metrics.registry).decode()
        assert 'container_metric_name="cpu_util"' in text
        assert 'value_type="current"' in text and 'value_type="pct"' not in text
        metrics.forget(["k1"])
        assert "k1" not in generate_latest(metrics.registry).decode()
