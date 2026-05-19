from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, Self
from uuid import UUID

from ai.backend.common.dto.clients.prometheus.response import (
    MetricResponseInfo,
    PrometheusResponse,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import KernelId
from ai.backend.manager.clients.prometheus.preset import MetricPreset
from ai.backend.manager.clients.prometheus.types import MetricValue, ValueType

__all__ = [
    "ContainerLiveStatQueries",
    "ContainerMetricOptionalLabel",
    "ContainerMetricResponseInfo",
    "ContainerMetricResult",
    "DIFF_METRICS",
    "KernelLiveStatBatchResult",
    "KernelLiveStatValues",
    "LiveStatRawValue",
    "MetricName",
    "MetricValue",
    "MetricResultValue",
    "RATE_METRICS",
    "MetricType",
    "ValueType",
]


# Backend.AI container metric name (e.g. "cpu_util", "mem", "cuda_mem").
type MetricName = str
# Raw Prometheus sample value, kept as the string Prometheus returned.
type LiveStatRawValue = str


class MetricType(StrEnum):
    """
    Specifies the type of a metric value.
    """

    GAUGE = "gauge"
    """
    Represents an instantly measured occupancy value.
    (e.g., used space as bytes, occupied amount as the number of items or a bandwidth)
    """
    RATE = "rate"
    """
    Represents a rate of changes calculated from underlying gauge/accumulation values
    (e.g., I/O bps calculated from RX/TX accum.bytes)
    """
    DIFF = "diff"
    """
    Represents a difference of changes calculated from underlying gauge/accumulation values
    (e.g., Utilization msec from CPU usage)
    """


@dataclass(frozen=True)
class ContainerLiveStatQueries:
    """PromQL queries for container live stats."""

    instant: MetricPreset
    rate_current: MetricPreset
    max: MetricPreset
    rate_max: MetricPreset
    avg: MetricPreset
    rate_avg: MetricPreset


DIFF_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})
RATE_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})


@dataclass
class ContainerMetricResponseInfo:
    value_type: str
    container_metric_name: str | None
    agent_id: str | None
    instance: str | None
    job: str | None
    kernel_id: str | None
    owner_project_id: str | None
    owner_user_id: str | None
    session_id: str | None

    @classmethod
    def from_metric_response_info(cls, info: MetricResponseInfo) -> Self:
        if info.value_type is None:
            raise InvalidAPIParameters(
                f"Missing required label 'value_type' for container metric (metric={info.name!r})"
            )
        return cls(
            value_type=info.value_type,
            container_metric_name=info.container_metric_name,
            agent_id=info.agent_id,
            instance=info.instance,
            job=info.job,
            kernel_id=info.kernel_id,
            owner_project_id=info.owner_project_id,
            owner_user_id=info.owner_user_id,
            session_id=info.session_id,
        )


@dataclass
class MetricResultValue:
    timestamp: float
    value: str


@dataclass
class ContainerMetricOptionalLabel:
    value_type: ValueType

    agent_id: str | None = None
    kernel_id: UUID | None = None
    session_id: UUID | None = None
    user_id: UUID | None = None
    project_id: UUID | None = None


@dataclass
class ContainerMetricResult:
    metric: ContainerMetricResponseInfo
    values: list[MetricResultValue]


@dataclass
class KernelLiveStatValues:
    """Per-kernel live-stat values partitioned by source query."""

    instant_current: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)
    instant_capacity: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)
    rate_current: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)
    max: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)
    rate_max: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)
    avg: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)
    rate_avg: dict[MetricName, LiveStatRawValue] = field(default_factory=dict)


@dataclass(frozen=True)
class KernelLiveStatBatchResult:
    """Live-stat values for a batch of kernels."""

    by_kernel: dict[KernelId, KernelLiveStatValues]

    @classmethod
    def empty(cls, kernel_ids: Sequence[KernelId]) -> Self:
        return cls(by_kernel={kid: KernelLiveStatValues() for kid in kernel_ids})

    @classmethod
    def from_responses(
        cls,
        *,
        instant: PrometheusResponse,
        rate_current: PrometheusResponse,
        max: PrometheusResponse,
        rate_max: PrometheusResponse,
        avg: PrometheusResponse,
        rate_avg: PrometheusResponse,
    ) -> Self:
        by_kernel: defaultdict[KernelId, KernelLiveStatValues] = defaultdict(KernelLiveStatValues)

        for kid, name, raw in cls._parse_samples(instant, value_type=ValueType.CURRENT.value):
            by_kernel[kid].instant_current[name] = raw
        for kid, name, raw in cls._parse_samples(instant, value_type=ValueType.CAPACITY.value):
            by_kernel[kid].instant_capacity[name] = raw
        for kid, name, raw in cls._parse_samples(rate_current):
            by_kernel[kid].rate_current[name] = raw
        for kid, name, raw in cls._parse_samples(max):
            by_kernel[kid].max[name] = raw
        for kid, name, raw in cls._parse_samples(rate_max):
            by_kernel[kid].rate_max[name] = raw
        for kid, name, raw in cls._parse_samples(avg):
            by_kernel[kid].avg[name] = raw
        for kid, name, raw in cls._parse_samples(rate_avg):
            by_kernel[kid].rate_avg[name] = raw

        return cls(by_kernel=dict(by_kernel))

    @staticmethod
    def _parse_samples(
        response: PrometheusResponse,
        *,
        value_type: str | None = None,
    ) -> list[tuple[KernelId, MetricName, LiveStatRawValue]]:
        samples: list[tuple[KernelId, MetricName, LiveStatRawValue]] = []
        for metric in response.data.result:
            info = metric.metric
            # The instant query mixes value_type=current and capacity in one response; this filter picks one.
            if value_type is not None and info.value_type != value_type:
                continue
            # Skip rows missing the (kernel, metric_name) identity or carrying no sample at all.
            if info.kernel_id is None or info.container_metric_name is None or not metric.values:
                continue
            # Skip when the kernel_id label is not a parseable UUID (defensive against malformed series).
            try:
                kernel_id = KernelId(UUID(info.kernel_id))
            except ValueError:
                continue
            # Instant queries return a one-element list; range queries are time-ordered, so [-1] is newest.
            _, raw_value = metric.values[-1]
            samples.append((kernel_id, info.container_metric_name, raw_value))
        return samples
