"""stat bridge: kernel statistics in the Agent's Valkey format, from the kubelet (suggestion 11.4).

The Manager, WebUI and idle checker read them unchanged. The kubelet's resource metrics carry
CPU time and memory; network and I/O stay empty until a Prometheus source is added.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Final

import msgpack
from aiohttp import web
from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

from ai.backend.agent.stats import Measurement, Metric, MetricTypes, MovingStatistics
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    CONTAINER_UTILIZATION_METRIC_NAME,
)
from ai.backend.common.types import MetricKey
from ai.backend.kube.controller.naming import (
    KERNEL_CONTAINER,
    LABEL_KERNEL_ID,
    LABEL_MANAGED_BY,
    LABEL_PROJECT_ID,
    LABEL_SESSION_ID,
    LABEL_USER_ID,
    MANAGED_BY,
)
from ai.backend.kube.scheduler.snapshot import pod_requests
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

STAT_INTERVAL: Final = 5.0
_CPU_SAMPLE: Final = "container_cpu_usage_seconds_total"
_MEM_SAMPLE: Final = "container_memory_working_set_bytes"
_Q: Final = Decimal("0.000")
_UNDEFINED: Final = "undefined"


@dataclass(frozen=True)
class ContainerSample:
    cpu_msec: Decimal
    mem_bytes: Decimal
    timestamp_ms: int  # when the kubelet took the CPU sample


def parse_resource_metrics(text: str) -> dict[tuple[str, str], dict[str, tuple[Decimal, int]]]:
    """`(namespace, pod)` of each kernel container → its CPU and memory samples (value, ms)."""
    samples: dict[tuple[str, str], dict[str, tuple[Decimal, int]]] = defaultdict(dict)
    for line in text.splitlines():
        if not line.startswith((_CPU_SAMPLE, _MEM_SAMPLE)):
            continue
        name, _, rest = line.partition("{")
        raw_labels, _, values = rest.partition("}")
        labels = dict(part.split("=", 1) for part in raw_labels.split(",") if "=" in part)
        if labels.get("container", "").strip('"') != KERNEL_CONTAINER:
            continue
        key = (labels["namespace"].strip('"'), labels["pod"].strip('"'))
        value, *timestamp = values.split()
        samples[key][name] = (Decimal(value), int(timestamp[0]) if timestamp else 0)
    return samples


def _mem_limit(pod: Mapping[str, Any]) -> Decimal:
    return Decimal(pod_requests(pod).memory)


class KernelStats:
    """The Agent's metrics of one kernel: `cpu_util`, `cpu_used`, `mem`."""

    _metrics: dict[MetricKey, Metric]
    _last: ContainerSample | None
    raw: dict[MetricKey, Measurement]  # the measurements as the Agent exports them to Prometheus

    def __init__(self) -> None:
        self._metrics = {}
        self._last = None
        self.raw = {}

    def update(self, sample: ContainerSample, mem_capacity: Decimal) -> bool:
        """Whether the sample is new. The kubelet refreshes its samples every 10~15 seconds, so
        `cpu_util` is the CPU time over the samples' own interval, not over our polling."""
        last, self._last = self._last, sample
        if last is not None and last.timestamp_ms == sample.timestamp_ms:
            return False
        # Prometheus gets the cumulative CPU time as `cpu_util`; the Manager takes its rate().
        self.raw = {
            MetricKey("cpu_util"): Measurement(sample.cpu_msec.quantize(_Q), Decimal(1000)),
            MetricKey("cpu_used"): Measurement(sample.cpu_msec.quantize(_Q)),
            MetricKey("mem"): Measurement(sample.mem_bytes, mem_capacity),
        }
        if last is not None and sample.timestamp_ms > last.timestamp_ms:
            used = max(sample.cpu_msec - last.cpu_msec, Decimal(0))
            millicores = used * 1000 / (sample.timestamp_ms - last.timestamp_ms)
            self._observe(
                MetricKey("cpu_util"),
                MetricTypes.UTILIZATION,
                "millicores",
                Measurement(millicores.quantize(_Q), capacity=Decimal(1000)),
                frozenset({"avg", "max"}),
            )
        self._observe(
            MetricKey("cpu_used"),
            MetricTypes.ACCUMULATION,
            "msec",
            Measurement(sample.cpu_msec.quantize(_Q)),
            frozenset(),
        )
        self._observe(
            MetricKey("mem"),
            MetricTypes.GAUGE,
            "bytes",
            Measurement(sample.mem_bytes, capacity=mem_capacity),
            frozenset({"max"}),
        )
        return True

    def _observe(
        self,
        key: MetricKey,
        type_: MetricTypes,
        unit: str,
        measure: Measurement,
        stats_filter: frozenset[str],
    ) -> None:
        if key in self._metrics:
            self._metrics[key].update(measure)
            return
        self._metrics[key] = Metric(
            key,
            type_,
            current=measure.value,
            capacity=measure.capacity or measure.value,
            unit_hint=unit,
            stats=MovingStatistics(measure.value),
            stats_filter=stats_filter,
        )

    def packed(self) -> bytes:
        packed: bytes = msgpack.packb({
            k: m.to_serializable_dict() for k, m in self._metrics.items()
        })
        return packed


class ContainerMetrics:
    """`backendai_container_utilization` as the Agent exports it; the Manager's live stats and
    Prometheus query presets read it."""

    registry: CollectorRegistry
    _gauge: Gauge
    _agent_id: str
    _labels: dict[str, set[tuple[str, ...]]]  # kernel id → label values set on the gauge

    def __init__(self, agent_id: str) -> None:
        self.registry = CollectorRegistry()
        self._agent_id = agent_id
        self._labels = defaultdict(set)
        self._gauge = Gauge(
            CONTAINER_UTILIZATION_METRIC_NAME,
            "Container utilization metrics",
            [
                CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
                "agent_id",
                "kernel_id",
                "session_id",
                "user_id",
                "project_id",
                "value_type",
            ],
            registry=self.registry,
        )

    def observe(
        self, labels: Mapping[str, str], kernel_id: str, raw: Mapping[MetricKey, Measurement]
    ) -> None:
        for key, measure in raw.items():
            pairs = [("current", measure.value)]
            if measure.capacity is not None:
                pairs.append(("capacity", measure.capacity))
            for value_type, value in pairs:
                label_values = (
                    key,
                    self._agent_id,
                    kernel_id,
                    labels.get(LABEL_SESSION_ID, _UNDEFINED),
                    labels.get(LABEL_USER_ID, _UNDEFINED),
                    labels.get(LABEL_PROJECT_ID, _UNDEFINED),
                    value_type,
                )
                self._gauge.labels(*label_values).set(float(value))
                self._labels[kernel_id].add(label_values)

    def forget(self, kernel_ids: Iterable[str]) -> None:
        for kernel_id in kernel_ids:
            for label_values in self._labels.pop(kernel_id, set()):
                self._gauge.remove(*label_values)

    async def serve(self, port: int) -> web.AppRunner:
        async def metrics(_request: web.Request) -> web.Response:
            return web.Response(
                body=generate_latest(self.registry), headers={"Content-Type": CONTENT_TYPE_LATEST}
            )

        app = web.Application()
        app.router.add_get("/metrics", metrics)
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        return runner


class StatBridge:
    _api: client.ApiClient
    _core: client.CoreV1Api
    _valkey: ValkeyStatClient
    _kernels: dict[str, KernelStats]
    _metrics: ContainerMetrics
    _interval: float

    def __init__(
        self,
        api: client.ApiClient,
        valkey: ValkeyStatClient,
        metrics: ContainerMetrics,
        interval: float = STAT_INTERVAL,
    ) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._valkey = valkey
        self._metrics = metrics
        self._kernels = {}
        self._interval = interval

    async def run(self) -> None:
        while True:
            try:
                await self.collect()
            except (ApiException, OSError) as e:
                log.warning("kernel stat collection failed", exc_info=e)
            await asyncio.sleep(self._interval)

    async def collect(self) -> None:
        listed = await self._core.list_pod_for_all_namespaces(
            label_selector=f"{LABEL_MANAGED_BY}={MANAGED_BY},{LABEL_KERNEL_ID}"
        )
        pods = [self._api.sanitize_for_serialization(p) for p in listed.items]
        by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for pod in pods:
            node = pod.get("spec", {}).get("nodeName")
            if node and pod["status"].get("phase") == "Running":
                by_node[node].append(pod)
        updates: dict[str, bytes] = {}
        for node, node_pods in by_node.items():
            text = await self._core.connect_get_node_proxy_with_path(node, "metrics/resource")
            samples = parse_resource_metrics(text)
            for pod in node_pods:
                key = (pod["metadata"]["namespace"], pod["metadata"]["name"])
                if _CPU_SAMPLE not in samples.get(key, {}):
                    continue
                cpu_seconds, sampled_at = samples[key][_CPU_SAMPLE]
                mem_bytes, _ = samples[key].get(_MEM_SAMPLE, (Decimal(0), 0))
                kernel_id = pod["metadata"]["labels"][LABEL_KERNEL_ID]
                stats = self._kernels.setdefault(kernel_id, KernelStats())
                if not stats.update(
                    ContainerSample(cpu_seconds * 1000, mem_bytes, sampled_at), _mem_limit(pod)
                ):
                    continue
                updates[kernel_id] = stats.packed()
                self._metrics.observe(pod["metadata"]["labels"], kernel_id, stats.raw)
        self._forget(pod["metadata"]["labels"][LABEL_KERNEL_ID] for pod in pods)
        if updates:
            await self._valkey.set_multiple_keys(updates)
        log.debug("kernel stats written", kernels=len(updates))

    def _forget(self, live: Iterable[str]) -> None:
        """Drop the moving statistics of kernels that are gone; their last values stay in Valkey."""
        alive = set(live)
        gone = [k for k in self._kernels if k not in alive]
        for kernel_id in gone:
            del self._kernels[kernel_id]
        self._metrics.forget(gone)
