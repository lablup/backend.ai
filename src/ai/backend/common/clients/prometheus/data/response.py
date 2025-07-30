from dataclasses import dataclass, field
from typing import Optional


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
    result: list[Result]


@dataclass
class LabelValueQueryResponseData:
    status: str
    data: list[str]
