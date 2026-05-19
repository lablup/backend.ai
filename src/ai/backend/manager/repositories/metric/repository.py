import logging
from collections.abc import Sequence

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.exception import (
    BackendAIError,
    FailedToGetMetric,
    PrometheusConnectionError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
    KernelLiveStatBatchResult,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

metric_repository_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.REPOSITORY, layer=LayerType.METRIC_REPOSITORY)),
        RetryPolicy(
            RetryArgs(
                max_retries=10,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class MetricRepository:
    _db: ExtendedAsyncSAEngine
    _prometheus_client: PrometheusClient

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        prometheus_client: PrometheusClient,
    ) -> None:
        self._db = db
        self._prometheus_client = prometheus_client

    async def query_container_metric_metadata(self) -> list[str]:
        return await self._prometheus_client.fetch_available_container_metric_names()

    async def query_container_metric(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
        time_range: QueryTimeRange,
    ) -> list[ContainerMetricResult]:
        return await self._prometheus_client.fetch_container_metric(metric_name, label, time_range)

    async def query_container_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> KernelLiveStatBatchResult:
        """Query metric backend for live stats of the given kernels."""
        if not kernel_ids:
            return KernelLiveStatBatchResult.empty(kernel_ids)
        try:
            return await self._prometheus_client.fetch_container_live_stats(kernel_ids)
        except (PrometheusConnectionError, FailedToGetMetric) as e:
            log.warning("Failed to query metrics for kernel live stats: {!r}", e)
            return KernelLiveStatBatchResult.empty(kernel_ids)
