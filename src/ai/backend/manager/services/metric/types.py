from dataclasses import dataclass
from typing import (
    Optional,
)
from uuid import UUID

from ai.backend.common.types import HostPortPair


@dataclass
class MetricQueryParameter:
    metric_name: str
    value_type: str
    start: str
    end: str
    step: str


@dataclass
class ServiceInitParameter:
    metric_query_addr: HostPortPair


@dataclass
class ContainerMetricResponseInfo:
    agent_id: str
    container_metric_name: str
    instance: str
    job: str
    kernel_id: str
    owner_project_id: str
    owner_user_id: str
    session_id: str
    value_type: str


@dataclass
class MetricResultValue:
    timestamp: float
    value: str


@dataclass
class ContainerMetricOptionalLabel:
    agent_id: Optional[str] = None
    kernel_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None


@dataclass
class ContainerMetricResult:
    metric: ContainerMetricResponseInfo
    values: list[MetricResultValue]
