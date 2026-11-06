<<<<<<< HEAD
import logging

from ai.backend.logging import BraceStyleAdapter
=======
from ai.backend.common.types import KernelId
from ai.backend.manager.clients.prometheus.metric_types import ensure_container_metric_name
>>>>>>> a449af324 (fix(BA-8876): reject a container metric name holding anything but letters, digits and underscores (#16465))
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from .actions.live_stat import ContainerLiveStatAction, ContainerLiveStatActionResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class MetricService:
    _metric_repository: MetricRepository

    def __init__(
        self,
        metric_repository: MetricRepository,
    ) -> None:
        self._metric_repository = metric_repository

    async def query_container_metric_metadata(
        self,
        _action: ContainerMetricMetadataAction,
    ) -> ContainerMetricMetadataActionResult:
        metric_names = await self._metric_repository.query_container_metric_metadata()
        return ContainerMetricMetadataActionResult(metric_names=metric_names)

    async def query_container_metric(
        self,
<<<<<<< HEAD
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
=======
        action: SearchUserContainerMetricsAction,
    ) -> SearchUserContainerMetricsActionResult:
        ensure_container_metric_name(action.metric_name)
        result = await self._metric_repository.query_container_metric(
            action.metric_name,
            action.labels(),
            action.time_range,
        )
        return SearchUserContainerMetricsActionResult(result=result)

    async def global_search_container_metrics(
        self,
        action: GlobalSearchContainerMetricsAction,
    ) -> GlobalSearchContainerMetricsActionResult:
        ensure_container_metric_name(action.metric_name)
>>>>>>> a449af324 (fix(BA-8876): reject a container metric name holding anything but letters, digits and underscores (#16465))
        result = await self._metric_repository.query_container_metric(
            action.metric_name,
            action.labels,
            action.time_range,
        )
        return ContainerMetricActionResult(result=result)

    async def query_container_live_stats(
        self,
        action: ContainerLiveStatAction,
    ) -> ContainerLiveStatActionResult:
        stats = await self._metric_repository.query_container_live_stats(action.kernel_ids)
        return ContainerLiveStatActionResult(stats=stats)
