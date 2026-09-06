from ai.backend.common.types import KernelId
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.services.metric.actions.batch_get_kernel_live_stats import (
    BatchGetKernelLiveStatsAction,
    BatchGetKernelLiveStatsActionResult,
)
from ai.backend.manager.services.metric.actions.search_container_metric_metadata import (
    PublicSearchContainerMetricMetadataAction,
    PublicSearchContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.actions.search_container_metrics import (
    PublicSearchContainerMetricsAction,
    PublicSearchContainerMetricsActionResult,
)


class MetricService:
    _metric_repository: MetricRepository

    def __init__(
        self,
        metric_repository: MetricRepository,
    ) -> None:
        self._metric_repository = metric_repository

    async def search_container_metric_metadata(
        self,
        _action: PublicSearchContainerMetricMetadataAction,
    ) -> PublicSearchContainerMetricMetadataActionResult:
        metric_names = await self._metric_repository.query_container_metric_metadata()
        return PublicSearchContainerMetricMetadataActionResult(metric_names=metric_names)

    async def search_container_metrics(
        self,
        action: PublicSearchContainerMetricsAction,
    ) -> PublicSearchContainerMetricsActionResult:
        result = await self._metric_repository.query_container_metric(
            action.metric_name,
            action.labels,
            action.time_range,
        )
        return PublicSearchContainerMetricsActionResult(result=result)

    async def batch_get_kernel_live_stats(
        self,
        action: BatchGetKernelLiveStatsAction,
    ) -> BatchGetKernelLiveStatsActionResult:
        stats = await self._metric_repository.query_container_live_stats([
            KernelId(kernel_id) for kernel_id in action.kernel_ids
        ])
        return BatchGetKernelLiveStatsActionResult(stats=stats)
