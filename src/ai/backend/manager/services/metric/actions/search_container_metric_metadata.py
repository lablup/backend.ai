from dataclasses import dataclass
from typing import override

from ai.backend.manager.services.metric.actions.base import QueryMetricAction


@dataclass(frozen=True)
class PublicSearchContainerMetricMetadataAction(QueryMetricAction):
    """List the container metric names the store holds; every authenticated user may."""

    @override
    @classmethod
    def action_name(cls) -> str:
        return "public_search_container_metric_metadata"


@dataclass(frozen=True)
class PublicSearchContainerMetricMetadataActionResult:
    metric_names: list[str]
