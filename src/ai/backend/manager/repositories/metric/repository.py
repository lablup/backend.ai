import logging
from collections.abc import Sequence

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.types import MetricValue
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
from ai.backend.manager.clients.prometheus.fixed_query_builder import FixedQueryBuilder
from ai.backend.manager.data.metric.types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    KernelLiveStatBatchResult,
    KernelMetricValuesByKernel,
    MetricResultValue,
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
    _fixed_query_builder: FixedQueryBuilder

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        prometheus_client: PrometheusClient,
        fixed_query_builder: FixedQueryBuilder,
    ) -> None:
        self._db = db
        self._prometheus_client = prometheus_client
        self._fixed_query_builder = fixed_query_builder

    async def query_container_metric_metadata(self) -> list[str]:
        query = self._fixed_query_builder.get_container_metric_metadata_query()
        result = await self._prometheus_client.query_label_values(
            label_name=query.label_name,
            metric_match=query.metric_match,
        )
        return result.data

    async def query_container_metric(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
        time_range: QueryTimeRange,
    ) -> list[ContainerMetricResult]:
        query = self._fixed_query_builder.get_container_metric_query(metric_name, label)
        response = await self._prometheus_client.query_range(query, time_range)
        return [
            ContainerMetricResult(
                metric=ContainerMetricResponseInfo.from_metric_response_info(m.metric),
                values=[MetricResultValue(*value) for value in m.values],
            )
            for m in response.data.result
        ]

    async def query_container_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> KernelLiveStatBatchResult:
        """Query Prometheus for live stats of the given kernels."""
        if not kernel_ids:
            return KernelLiveStatBatchResult.empty(kernel_ids)
        try:
            values_by_kernel = await self._query_container_live_stats(kernel_ids)
        except (PrometheusConnectionError, FailedToGetMetric):
            log.warning("Failed to query Prometheus for kernel live stats, returning empty results")
            return KernelLiveStatBatchResult.empty(kernel_ids)
        return KernelLiveStatBatchResult.from_metric_values(kernel_ids, values_by_kernel)

    async def _query_container_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, list[MetricValue]]:
        live_stat_queries = self._fixed_query_builder.get_container_live_stat_queries(kernel_ids)
        merged = KernelMetricValuesByKernel(values_by_kernel={})
        for query in live_stat_queries.to_list():
            try:
                response = await self._prometheus_client.query_instant(query)
            except (PrometheusConnectionError, FailedToGetMetric) as e:
                log.warning("Failed to query Prometheus for live stat preset, skipping: {}", e)
                continue
            merged = merged.merged_with(
                KernelMetricValuesByKernel.from_prometheus_response(response)
            )
        return merged.values_by_kernel
