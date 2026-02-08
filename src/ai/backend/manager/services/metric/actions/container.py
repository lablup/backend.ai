from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.metric.types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
)


@dataclass
class ContainerMetricMetadataAction(BaseAction):
    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_METRIC_METADATA

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ContainerMetricMetadataActionResult(BaseActionResult):
    metric_names: list[str]

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class ContainerMetricAction(BaseAction):
    metric_name: str
    labels: ContainerMetricOptionalLabel

    start: str
    end: str
    step: str

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_METRIC

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class ContainerMetricActionResult(BaseActionResult):
    result: list[ContainerMetricResult]

    @override
    def entity_id(self) -> str | None:
        return None
