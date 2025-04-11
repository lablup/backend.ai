from dataclasses import dataclass

from ..types import ContainerMetricOptionalLabel, ContainerMetricResult
from .base import MetricAction, MetricActionResult


@dataclass
class ContainerMetricMetadataAction(MetricAction):
    def entity_type(self) -> str:
        return "metric"

    def operation_type(self) -> str:
        return "query"


@dataclass
class ContainerMetricMetadataActionResult(MetricActionResult):
    metric_names: list[str]


@dataclass
class ContainerMetricAction(MetricAction):
    metric_name: str
    labels: ContainerMetricOptionalLabel

    start: str
    end: str
    step: str

    def entity_type(self) -> str:
        return "metric"

    def operation_type(self) -> str:
        return "query"


@dataclass
class ContainerMetricActionResult(MetricActionResult):
    result: list[ContainerMetricResult]
