from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult

from ..types import ContainerMetricOptionalLabel, ContainerMetricResult


@dataclass
class ContainerMetricMetadataAction(BaseAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "container_metric_metadata"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "query"


@dataclass
class ContainerMetricMetadataActionResult(BaseActionResult):
    metric_names: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class ContainerMetricAction(BaseAction):
    metric_name: str
    labels: ContainerMetricOptionalLabel

    start: str
    end: str
    step: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "container_metric"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "query"


@dataclass
class ContainerMetricActionResult(BaseActionResult):
    result: list[ContainerMetricResult]

    @override
    def entity_id(self) -> Optional[str]:
        return None
