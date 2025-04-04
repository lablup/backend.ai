from dataclasses import dataclass
from typing import (
    Optional,
)
from uuid import UUID

from ai.backend.common.types import HostPortPair


@dataclass
class MetricQueryParameter:
    metric_name: str
    value_type: Optional[str]
    start: str
    end: str
    step: str


@dataclass
class ServiceInitParameter:
    metric_query_addr: HostPortPair


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
