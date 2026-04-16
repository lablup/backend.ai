from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Final, Self
from uuid import UUID

from pydantic import BaseModel

from ai.backend.common.dto.clients.prometheus.response import (
    MetricResponseInfo,
    PrometheusResponse,
)
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import KernelId
from ai.backend.manager.data.metric.types import (
    KernelLiveStatBatchResult as KernelLiveStatBatchResult,
)
from ai.backend.manager.data.metric.types import (
    KernelLiveStatEntry as KernelLiveStatEntry,
)
from ai.backend.manager.data.metric.types import (
    KernelMetricValue,
)
from ai.backend.manager.data.metric.types import (
    ValueType as ValueType,
)


class MetricQueryParameter(BaseModel):
    metric_name: str
    value_type: ValueType
    start: str
    end: str
    step: str


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
class KernelMetricValuesByKernel:
    values_by_kernel: dict[KernelId, list[KernelMetricValue]]

    @classmethod
    def from_prometheus_response(cls, response: PrometheusResponse) -> Self:
        grouped: dict[KernelId, list[KernelMetricValue]] = {}
        for metric in response.data.result:
            info = metric.metric
            if (
                info.kernel_id is None
                or info.container_metric_name is None
                or info.value_type is None
                or not metric.values
            ):
                continue
            try:
                value_type = ValueType(info.value_type)
                kernel_id = KernelId(UUID(info.kernel_id))
            except ValueError:
                continue
            # Instant queries are normalized into a one-element list, and range
            # queries are ordered by time, so the last sample is the newest one.
            _, raw_value = metric.values[-1]
            grouped.setdefault(kernel_id, []).append(
                KernelMetricValue(
                    metric_name=info.container_metric_name,
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


class UtilizationMetricType(enum.Enum):
    """
    Specifies the type of a metric value.
    """

    GAUGE = enum.auto()
    """
    Represents an instantly measured occupancy value.
    (e.g., used space as bytes, occupied amount as the number of items or a bandwidth)
    """
    RATE = enum.auto()
    """
    Represents a rate of changes calculated from underlying gauge/accumulation values
    (e.g., I/O bps calculated from RX/TX accum.bytes)
    """
    DIFF = enum.auto()
    """
    Represents a difference of changes calculated from underlying gauge/accumulation values
    (e.g., Utilization msec from CPU usage)
    """


# Metric-name -> UtilizationMetricType classification rules.
# TODO: Refactor to query metric metadata from the repository layer once
#       the metadata persistence is available.
DIFF_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})
RATE_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})
