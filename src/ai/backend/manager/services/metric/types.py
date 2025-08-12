import enum
from dataclasses import dataclass
from typing import (
    Optional,
    Self,
)
from uuid import UUID

from pydantic import BaseModel

from ai.backend.common.clients.prometheus.container_util.data.response import (
    ContainerUtilizationQueryResult,
)
from ai.backend.common.clients.prometheus.data.response import ResultMetric
from ai.backend.common.clients.prometheus.device_util.data.response import (
    DeviceUtilizationQueryResult,
)


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

    @classmethod
    def from_result_metric(cls, result_metric: "ResultMetric") -> Self:
        return cls(
            value_type=result_metric.value_type,
            container_metric_name=result_metric.container_metric_name,
            agent_id=result_metric.agent_id,
            instance=result_metric.instance,
            job=result_metric.job,
            kernel_id=result_metric.kernel_id,
            owner_project_id=result_metric.owner_project_id,
            owner_user_id=result_metric.owner_user_id,
            session_id=result_metric.session_id,
        )


@dataclass
class MetricResultValue:
    timestamp: float
    value: str


@dataclass
class ContainerMetricOptionalLabel:
    value_type: Optional[ValueType]

    container_metric_name: Optional[str] = None
    agent_id: Optional[str] = None
    kernel_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


@dataclass
class ContainerMetricResult:
    metric: ContainerMetricResponseInfo
    values: list[MetricResultValue]

    @classmethod
    def from_result(cls, result: ContainerUtilizationQueryResult) -> Self:
        return cls(
            metric=ContainerMetricResponseInfo.from_result_metric(result.metric),
            values=[
                MetricResultValue(timestamp=value.timestamp, value=value.value)
                for value in result.values
            ],
        )


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


@dataclass
class DeviceMetricResponseInfo:
    value_type: str
    device_metric_name: Optional[str]
    agent_id: Optional[str]
    device_id: Optional[str]

    instance: Optional[str]
    job: Optional[str]

    @classmethod
    def from_result_metric(cls, result_metric: "ResultMetric") -> Self:
        return cls(
            value_type=result_metric.value_type,
            device_metric_name=result_metric.device_metric_name,
            agent_id=result_metric.agent_id,
            device_id=result_metric.device_id,
            instance=result_metric.instance,
            job=result_metric.job,
        )


@dataclass
class DeviceMetricOptionalLabel:
    value_type: Optional[ValueType]
    device_metric_name: Optional[str]
    agent_id: Optional[str]
    device_id: Optional[str]


@dataclass
class DeviceMetricResult:
    metric: DeviceMetricResponseInfo
    values: list[MetricResultValue]

    @classmethod
    def from_result(cls, result: DeviceUtilizationQueryResult) -> Self:
        return cls(
            metric=DeviceMetricResponseInfo.from_result_metric(result.metric),
            values=[
                MetricResultValue(timestamp=value.timestamp, value=value.value)
                for value in result.values
            ],
        )
