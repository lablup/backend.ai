from __future__ import annotations

from decimal import Decimal
from typing import Any

import msgpack
from prometheus_client import generate_latest

from ai.backend.kube.controller.stats import (
    ContainerMetrics,
    ContainerSample,
    KernelStats,
    kubelet_endpoint,
    parse_stats_summary,
)

SUMMARY: dict[str, Any] = {
    "node": {"nodeName": "n1"},
    "pods": [
        {
            "podRef": {"name": "s-1-main1", "namespace": "ns"},
            "containers": [
                {
                    "name": "kernel",
                    "cpu": {"time": "2023-11-14T22:13:20Z", "usageCoreNanoSeconds": 2500000000},
                    "memory": {"workingSetBytes": 1048576},
                },
                {
                    "name": "krunner",
                    "cpu": {"time": "2023-11-14T22:13:20Z", "usageCoreNanoSeconds": 100},
                },
            ],
        },
        {
            "podRef": {"name": "s-2-main1", "namespace": "ns"},
            "containers": [{"name": "kernel", "cpu": {"time": "2023-11-14T22:13:20Z"}}],
        },
    ],
}


class TestParseStatsSummary:
    def test_keeps_only_kernel_containers_with_a_cpu_sample(self) -> None:
        assert parse_stats_summary(SUMMARY) == {
            ("ns", "s-1-main1"): ContainerSample(
                cpu_msec=Decimal(2500), mem_bytes=Decimal(1048576), timestamp_ms=1700000000000
            )
        }


class TestKubeletEndpoint:
    def test_internal_ip_and_kubelet_port(self) -> None:
        node = {
            "status": {
                "addresses": [
                    {"type": "Hostname", "address": "n1"},
                    {"type": "InternalIP", "address": "10.0.0.5"},
                ],
                "daemonEndpoints": {"kubeletEndpoint": {"Port": 10255}},
            }
        }
        assert kubelet_endpoint(node) == "https://10.0.0.5:10255"

    def test_ipv6_address_is_bracketed(self) -> None:
        node = {"status": {"addresses": [{"type": "InternalIP", "address": "fd00::5"}]}}
        assert kubelet_endpoint(node) == "https://[fd00::5]:10250"

    def test_a_node_without_an_internal_ip_has_none(self) -> None:
        assert kubelet_endpoint({"status": {"addresses": []}}) is None


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
