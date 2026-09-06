from dataclasses import dataclass
from typing import override

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
)
from ai.backend.manager.services.metric.actions.base import QueryMetricAction


@dataclass(frozen=True)
class GlobalSearchContainerMetricsAction(QueryMetricAction):
    """Read one container metric over a time range, narrowed by whatever labels are given.

    Names no user, so it reads across all of them and stays behind the global gate.
    """

    metric_name: str
    labels: ContainerMetricOptionalLabel
    time_range: QueryTimeRange

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_container_metrics"


@dataclass(frozen=True)
class GlobalSearchContainerMetricsActionResult:
    result: list[ContainerMetricResult]
