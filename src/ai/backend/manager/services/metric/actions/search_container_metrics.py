from dataclasses import dataclass
from typing import override

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
)
from ai.backend.manager.services.metric.actions.base import QueryMetricAction


@dataclass(frozen=True)
class PublicSearchContainerMetricsAction(QueryMetricAction):
    """Read one container metric over a time range; every authenticated user may."""

    metric_name: str
    labels: ContainerMetricOptionalLabel
    time_range: QueryTimeRange

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_search_container_metrics"


@dataclass(frozen=True)
class PublicSearchContainerMetricsActionResult:
    result: list[ContainerMetricResult]
