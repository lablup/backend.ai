from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
)
from ai.backend.manager.services.metric.actions.base import (
    QueryMetricAction,
    QueryMetricActionResult,
)


@dataclass(frozen=True)
class ContainerMetricMetadataAction(QueryMetricAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_METRIC_METADATA


@dataclass(frozen=True)
class ContainerMetricMetadataActionResult(QueryMetricActionResult):
    metric_names: list[str]


@dataclass(frozen=True)
class ContainerMetricAction(QueryMetricAction):
    metric_name: str
    labels: ContainerMetricOptionalLabel
    time_range: QueryTimeRange

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.CONTAINER_METRIC


@dataclass(frozen=True)
class ContainerMetricActionResult(QueryMetricActionResult):
    result: list[ContainerMetricResult]
