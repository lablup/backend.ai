from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class QueryData:
    query: str
    start: Optional[str]
    end: Optional[str]
    step: Optional[str]


@dataclass
class ResultMetric:
    value_type: str
    name: Optional[str] = field(
        default=None,
    )
    agent_id: Optional[str] = field(default=None)
    container_metric_name: Optional[str] = field(default=None)
    instance: Optional[str] = field(default=None)
    job: Optional[str] = field(default=None)
    kernel_id: Optional[str] = field(default=None)
    owner_project_id: Optional[str] = field(default=None)
    service_group: Optional[str] = field(default=None)
    service_id: Optional[str] = field(default=None)
    session_id: Optional[str] = field(default=None)
    owner_user_id: Optional[str] = field(default=None)
    version: Optional[str] = field(default=None)

    device_metric_name: Optional[str] = field(default=None)
    device_id: Optional[str] = field(default=None)


@dataclass
class ResultValue:
    timestamp: float
    value: str


@dataclass
class Result:
    metric: Optional[ResultMetric]
    values: list[ResultValue]


@dataclass
class QueryResponseData:
    status: int
    result: list[Result]


@dataclass
class LabelValueResponse:
    status: str
    data: list[str]


@dataclass
class QueryRange:
    step: str
    start: Optional[datetime]
    end: Optional[datetime]

    @property
    def start_iso(self) -> Optional[str]:
        return self.start.isoformat() if self.start else None

    @property
    def end_iso(self) -> Optional[str]:
        return self.end.isoformat() if self.end else None


@dataclass
class ContainerUtilizationQueryParameter:
    value_type: Optional[str]
    container_metric_name: Optional[str] = None
    agent_id: Optional[str] = None
    kernel_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

    range: Optional[QueryRange] = None


@dataclass
class ContainerUtilizationQueryResult:
    metric: ResultMetric
    values: list[ResultValue]


@dataclass
class DeviceUtilizationQueryParameter:
    value_type: Optional[str]
    device_metric_name: Optional[str] = None
    agent_id: Optional[str] = None
    device_id: Optional[str] = None

    range: Optional[QueryRange] = None


@dataclass
class DeviceUtilizationQueryResult:
    metric: ResultMetric
    values: list[ResultValue]


@dataclass
class QueryStringSpec:
    metric_name: Optional[str]
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
