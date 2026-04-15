import enum
from dataclasses import dataclass
from typing import Final, Self
from uuid import UUID

from pydantic import BaseModel

from ai.backend.common.dto.clients.prometheus.response import MetricResponseInfo
from ai.backend.common.exception import InvalidAPIParameters


class ValueType(enum.StrEnum):
    """
    Specifies the type of a metric value.
    """

    CURRENT = "current"
    CAPACITY = "capacity"
    PCT = "pct"


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
class KernelMetricValue:
    """A single (current|capacity) value for one metric of one kernel."""

    metric_name: str
    value_type: ValueType
    value: str


@dataclass(frozen=True)
class KernelLiveStatEntry:
    """All live_stat samples belonging to a single kernel.

    An empty ``values`` list represents "no Prometheus samples yet" — callers
    do not need to handle ``None``; the entry is always present.
    """

    kernel_id: UUID
    values: list[KernelMetricValue]


@dataclass(frozen=True)
class KernelLiveStatBatchResult:
    """Per-kernel batch result for ``query_kernel_live_stat_batch``.

    Always contains one entry per requested ``kernel_id``. Missing data is
    represented as an empty ``KernelLiveStatEntry.values`` list, never ``None``.
    """

    entries: dict[UUID, KernelLiveStatEntry]


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


# Metric-name → UtilizationMetricType classification rules.
# TODO: Refactor to query metric metadata from the repository layer once
#       the metadata persistence is available.
DIFF_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})
RATE_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})
