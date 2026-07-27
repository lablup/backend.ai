import logging
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from uuid import UUID

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
from ai.backend.common.types import KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
    KernelLiveStatBatchResult,
)
from ai.backend.manager.data.metric.types import SessionUtilizationMetricResult
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.metric.types import SessionUtilizationMetricQuery

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

    async def query_session_utilization_metrics(
        self,
        query: SessionUtilizationMetricQuery,
    ) -> SessionUtilizationMetricResult:
        try:
            response = await self._prometheus_client.fetch_session_utilization(
                metric_name=query.metric_name,
                kernel_policy=query.kernel_policy,
                time_window_seconds=query.time_window_seconds,
                session_ids=query.session_ids,
                evaluation_time=query.evaluation_time.isoformat(),
            )
        except (PrometheusConnectionError, FailedToGetMetric) as e:
            log.warning(
                "Utilization query failed for metric {} and policy {}: {}",
                query.metric_name,
                query.kernel_policy,
                e,
            )
            return SessionUtilizationMetricResult(by_session={})
        values: dict[SessionId, Decimal] = {}
        for result in response.data.result:
            if result.metric.session_id is None or not result.values:
                continue
            try:
                session_id = SessionId(UUID(result.metric.session_id))
                value = Decimal(result.values[-1][1])
            except (ValueError, InvalidOperation):
                continue
            if not value.is_finite():
                continue
            if session_id in values:
                raise InternalServerError(
                    f"Utilization query returned multiple values for session {session_id}"
                )
            values[session_id] = value
        return SessionUtilizationMetricResult(by_session=values)
