from dataclasses import dataclass
from typing import (
    Final,
    Optional,
)
from uuid import UUID

DEFAULT_METRIC_QUERY_TIMEWINDOW: Final[str] = "1m"


@dataclass
class MetricQueryParameter:
    metric_name: str
    value_type: Optional[str]
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
    value_type: Optional[str] = None

    agent_id: Optional[str] = None
    kernel_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


@dataclass
class ContainerMetricResult:
    metric: ContainerMetricResponseInfo
    values: list[MetricResultValue]


@dataclass(kw_only=True)
class MetricSpecForQuery:
    metric_name: str
    timewindow: str = DEFAULT_METRIC_QUERY_TIMEWINDOW
    sum_by: Optional[str] = None
    labels: Optional[str] = None
