import enum
from dataclasses import dataclass, field
from typing import (
    Optional,
)
from uuid import UUID

from pydantic import BaseModel


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
    container_metric_name: Optional[str]
    agent_id: Optional[str]
    instance: Optional[str]
    job: Optional[str]
    kernel_id: Optional[str]
    owner_project_id: Optional[str]
    owner_user_id: Optional[str]
    session_id: Optional[str]


@dataclass
class MetricResultValue:
    timestamp: float
    value: str


@dataclass
class ContainerMetricOptionalLabel:
    value_type: ValueType

    agent_id: Optional[str] = None
    kernel_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


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
