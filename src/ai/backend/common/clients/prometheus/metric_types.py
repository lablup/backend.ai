from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Self, cast
from uuid import UUID

from ai.backend.common.clients.prometheus.preset import MetricPreset
from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.dto.clients.prometheus.response import (
    MetricResponseInfo,
    PrometheusResponse,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.metrics.types import CAPACITY_SENTINEL, CAPACITY_SENTINEL_METRICS
from ai.backend.common.types import KernelId

__all__ = [
    "ContainerLiveStatQueries",
    "ContainerMetricOptionalLabel",
    "ContainerMetricResponseInfo",
    "ContainerMetricResult",
    "DIFF_METRICS",
    "KernelLiveStatBatchResult",
    "KernelLiveStatEntry",
    "KernelLiveStatValues",
    "KernelMetricValuesByKernel",
    "MetricValue",
    "MetricResultValue",
    "RATE_METRICS",
    "MetricType",
    "ValueType",
]


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


# Metric-name -> MetricType classification rules.
# TODO: Refactor to query metric metadata from the repository layer once
#       the metadata persistence is available.


@dataclass(frozen=True)
class ContainerLiveStatQueries:
    """Gauge / diff / rate / max / avg / rate_stats query preset bundle for container live stats."""

    gauge: MetricPreset
    diff: MetricPreset
    rate: MetricPreset
    max: MetricPreset
    avg: MetricPreset
    rate_stats: MetricPreset

    def to_list(self) -> list[MetricPreset]:
        return [self.gauge, self.diff, self.rate, self.max, self.avg, self.rate_stats]


# Backend.AI accelerator/plugin gauge metric naming convention.
# Adding a new suffix here is the single edit needed to extend stats.{max,avg}
# coverage to a new family of accelerator metrics (e.g., adding "clock" auto-
# covers cuda_clock / gpu_clock / tpu_clock).
_ACCEL_GAUGE_SUFFIXES_MAX_ONLY: Final[frozenset[str]] = frozenset({"mem"})
_ACCEL_GAUGE_SUFFIXES_WITH_AVG: Final[frozenset[str]] = frozenset({
    "util",
    "power",
    "temperature",
})


def _accel_suffix_pattern(suffixes: frozenset[str]) -> str:
    body = "|".join(sorted(suffixes))
    return rf"[A-Za-z0-9][A-Za-z0-9_-]*_({body})"


DIFF_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})
RATE_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})

# Intrinsic gauge metrics that don't follow the accelerator suffix convention.
STATS_MAX_GAUGE_METRICS: Final[frozenset[str]] = frozenset({
    "mem",
    "io_scratch_size",
})
STATS_AVG_GAUGE_METRICS: Final[frozenset[str]] = frozenset()
# Pattern-based gauge coverage for plugin/accelerator metrics.
STATS_MAX_GAUGE_METRIC_PATTERNS: Final[frozenset[str]] = frozenset({
    _accel_suffix_pattern(_ACCEL_GAUGE_SUFFIXES_MAX_ONLY | _ACCEL_GAUGE_SUFFIXES_WITH_AVG),
})
STATS_AVG_GAUGE_METRIC_PATTERNS: Final[frozenset[str]] = frozenset({
    _accel_suffix_pattern(_ACCEL_GAUGE_SUFFIXES_WITH_AVG),
})
STATS_MAX_OVER_RATE_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})
STATS_AVG_OVER_RATE_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})

# stats.rate emission targets the legacy stats.rate live_stat label.
# Two metric shapes flow in:
#   * "gauge" set: agent's current_hook already publishes per-second rate as
#     the metric's `current` value, so we only need to sum across replicas
#     and relabel to stats.rate (no PromQL rate() wrap).
#   * "counter" set: the published series is a cumulative byte counter, so
#     we apply rate(...[window]) to get bytes/sec before relabel.
STATS_RATE_GAUGE_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})
STATS_RATE_COUNTER_METRICS: Final[frozenset[str]] = frozenset({"io_read", "io_write"})


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


@dataclass(frozen=True)
class KernelLiveStatEntry:
    """All live_stat samples belonging to a single kernel.

    An empty `values` list represents "no Prometheus samples yet"
    """

    kernel_id: KernelId
    values: list[MetricValue]


@dataclass(frozen=True)
class KernelLiveStatBatchResult:
    # Per-kernel bulk result for `query_container_live_stats`

    entries: dict[KernelId, KernelLiveStatEntry]

    @classmethod
    def empty(cls, kernel_ids: Sequence[KernelId]) -> Self:
        return cls.from_metric_values(kernel_ids, {})

    @classmethod
    def from_metric_values(
        cls,
        kernel_ids: Sequence[KernelId],
        values_by_kernel: Mapping[KernelId, Sequence[MetricValue]],
    ) -> Self:
        return cls(
            entries={
                kid: KernelLiveStatEntry(
                    kernel_id=kid,
                    values=list(values_by_kernel.get(kid, [])),
                )
                for kid in kernel_ids
            }
        )


@dataclass(frozen=True)
class KernelLiveStatValues:
    values_by_kernel: Mapping[KernelId, list[MetricValue]]

    @classmethod
    def with_capacity_sentinels(
        cls,
        values_by_kernel: Mapping[KernelId, list[MetricValue]],
    ) -> Self:
        """For live metrics without a meaningful capacity, synthesize capacity sentinels."""
        new_values: dict[KernelId, list[MetricValue]] = {
            kid: list(vs) for kid, vs in values_by_kernel.items()
        }
        for kid, vs in new_values.items():
            reported_currents: set[str] = {
                v.metric_name for v in vs if v.value_type is ValueType.CURRENT
            }
            sentinel_targets = reported_currents & CAPACITY_SENTINEL_METRICS
            if not sentinel_targets:
                continue
            rewritten: list[MetricValue] = []
            samples_to_keep = [
                v
                for v in vs
                if not (v.value_type is ValueType.CAPACITY and v.metric_name in sentinel_targets)
            ]
            rewritten.extend(samples_to_keep)
            for metric_name in sentinel_targets:
                rewritten.append(
                    MetricValue(
                        metric_name=metric_name,
                        value_type=ValueType.CAPACITY,
                        value=CAPACITY_SENTINEL,
                    )
                )
            new_values[kid] = rewritten
        return cls(values_by_kernel=new_values)


@dataclass(frozen=True)
class KernelMetricValuesByKernel:
    values_by_kernel: dict[KernelId, list[MetricValue]]

    @classmethod
    def from_prometheus_response(cls, response: PrometheusResponse) -> Self:
        grouped: dict[KernelId, list[MetricValue]] = {}
        for metric in response.data.result:
            info = metric.metric
            if not info.has_container_metric_labels or not metric.values:
                continue
            # Non-None guaranteed by has_container_metric_labels above;
            # cast needed because property checks don't narrow types.
            kernel_id_str = cast(str, info.kernel_id)
            container_metric_name = cast(str, info.container_metric_name)
            value_type_str = cast(str, info.value_type)
            try:
                value_type = ValueType(value_type_str)
                kernel_id = KernelId(UUID(kernel_id_str))
            except ValueError:
                continue
            # Instant queries are normalized into a one-element list, and range
            # queries are ordered by time, so the last sample is the newest one.
            _, raw_value = metric.values[-1]
            grouped.setdefault(kernel_id, []).append(
                MetricValue(
                    metric_name=container_metric_name,
                    value_type=value_type,
                    value=raw_value,
                )
            )
        return cls(values_by_kernel=grouped)

    def merged_with(self, other: Self) -> Self:
        merged = {kernel_id: list(values) for kernel_id, values in self.values_by_kernel.items()}
        for kernel_id, values in other.values_by_kernel.items():
            merged.setdefault(kernel_id, []).extend(values)
        return type(self)(values_by_kernel=merged)
