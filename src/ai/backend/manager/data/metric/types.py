from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Self, cast
from uuid import UUID

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.dto.clients.prometheus.response import (
    MetricResponseInfo,
    PrometheusResponse,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import KernelId

__all__ = [
    "ContainerMetricOptionalLabel",
    "ContainerMetricResponseInfo",
    "ContainerMetricResult",
    "DIFF_METRICS",
    "KernelLiveStatBatchResult",
    "KernelLiveStatEntry",
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
