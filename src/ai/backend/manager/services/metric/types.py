from dataclasses import dataclass
from typing import (
    Any,
    Optional,
)
from uuid import UUID


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

    def get_sum_by_for_query(self) -> list[str]:
        sum_by_values = ["value_type"]

        def _append_if_not_none(value: Any, name: str) -> None:
            if value is not None:
                sum_by_values.append(name)

        _append_if_not_none(self.agent_id, "agent_id")
        _append_if_not_none(self.kernel_id, "kernel_id")
        _append_if_not_none(self.session_id, "session_id")
        _append_if_not_none(self.user_id, "user_id")
        _append_if_not_none(self.project_id, "project_id")
        return sum_by_values

    def get_label_values_for_query(self, metric_name: str) -> list[str]:
        label_values: list[str] = [
            f'container_metric_name="{metric_name}"',
        ]

        def _append_if_not_none(value: Any, name: str) -> None:
            if value is not None:
                label_values.append(f'{name}="{value}"')

        _append_if_not_none(self.value_type, "value_type")
        _append_if_not_none(self.agent_id, "agent_id")
        _append_if_not_none(self.kernel_id, "kernel_id")
        _append_if_not_none(self.session_id, "session_id")
        _append_if_not_none(self.user_id, "user_id")
        _append_if_not_none(self.project_id, "project_id")
        return label_values


@dataclass
class ContainerMetricResult:
    metric: ContainerMetricResponseInfo
    values: list[MetricResultValue]
