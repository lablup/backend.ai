import logging

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.exception import (
    FailedToGetMetric,
    PrometheusConnectionError,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.metric.types import KernelLiveStatBatchResult
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .actions.live_stat import QueryKernelLiveStatAction, QueryKernelLiveStatActionResult
from .container_metric import (
    ContainerUtilizationMetricService,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class UtilizationMetricService:
    container: ContainerUtilizationMetricService
    _metric_repository: MetricRepository

    def __init__(
        self,
        prometheus_client: PrometheusClient,
        timewindow: str,
        metric_repository: MetricRepository,
    ) -> None:
        self.container = ContainerUtilizationMetricService(prometheus_client, timewindow=timewindow)
        self._metric_repository = metric_repository

    async def query_kernel_live_stat_batch(
        self,
        action: QueryKernelLiveStatAction,
    ) -> QueryKernelLiveStatActionResult:
        if not action.kernel_ids:
            return QueryKernelLiveStatActionResult(
                stats=KernelLiveStatBatchResult.empty(action.kernel_ids)
            )
        try:
            values_by_kernel = await self._metric_repository.query_kernel_live_stats(
                action.kernel_ids,
            )
        except (PrometheusConnectionError, FailedToGetMetric):
            log.warning("Failed to query Prometheus for kernel live stats, returning empty results")
            return QueryKernelLiveStatActionResult(
                stats=KernelLiveStatBatchResult.empty(action.kernel_ids)
            )

        return QueryKernelLiveStatActionResult(
            stats=KernelLiveStatBatchResult.from_metric_values(
                action.kernel_ids,
                values_by_kernel,
            )
        )
