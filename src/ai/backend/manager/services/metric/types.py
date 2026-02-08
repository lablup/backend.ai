import enum
from dataclasses import dataclass, field
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from ai.backend.common.dto.clients.prometheus.response import MetricResponseInfo


class ValueType(enum.StrEnum):
    """
    Specifies the type of a metric value.
    """

    CURRENT = "current"
    CAPACITY = "capacity"


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


@dataclass(kw_only=True)
class MetricSpecForQuery:
    metric_name: str
    metric_type: UtilizationMetricType
    timewindow: str
    sum_by: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)

    def str_sum_by(self) -> str:
        if not self.sum_by:
            return ""
        return f"sum by ({','.join(self.sum_by)})"

    def str_labels(self) -> str:
        if not self.labels:
            return ""
        return f"{{{','.join(self.labels)}}}"
