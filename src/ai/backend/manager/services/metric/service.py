import logging

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from .actions.live_stat import KernelLiveStatAction, KernelLiveStatActionResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UtilizationMetricService:
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
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        result = await self._metric_repository.query_container_metric(
            action.metric_name,
            action.labels,
            action.time_range,
        )
        return ContainerMetricActionResult(result=result)

    async def query_kernel_live_stat_batch(
        self,
        action: KernelLiveStatAction,
    ) -> KernelLiveStatActionResult:
        stats = await self._metric_repository.query_kernel_live_stat_batch(action.kernel_ids)
        return KernelLiveStatActionResult(stats=stats)
