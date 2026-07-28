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
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.repositories.metric.types import (
    SessionUtilizationMetricQuery,
    SessionUtilizationMetricResult,
)
from ai.backend.manager.repositories.prometheus_query_preset.db_source import (
    PrometheusQueryPresetDBSource,
)

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
    _prometheus_client: PrometheusClient
    _prometheus_query_preset_db_source: PrometheusQueryPresetDBSource

    def __init__(
        self,
        prometheus_client: PrometheusClient,
        prometheus_query_preset_db_source: PrometheusQueryPresetDBSource,
    ) -> None:
        self._prometheus_client = prometheus_client
        self._prometheus_query_preset_db_source = prometheus_query_preset_db_source

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
        preset = await self._prometheus_query_preset_db_source.get_by_id(query.preset_id)
        try:
            response = await self._prometheus_client.fetch_session_utilization(
                query_template=preset.query_template,
                time_window=preset.time_window or "",
                session_ids=query.session_ids,
                evaluation_time=query.evaluation_time.isoformat(),
            )
        except (PrometheusConnectionError, FailedToGetMetric) as e:
            log.warning(
                "Utilization query failed for preset {}: {}",
                query.preset_id,
                e,
            )
            return SessionUtilizationMetricResult(by_session={})
        requested_session_ids = set(query.session_ids)
        values: dict[SessionId, Decimal] = {}
        for result in response.data.result:
            if result.metric.session_id is None or not result.values:
                continue
            try:
                session_id = SessionId(UUID(result.metric.session_id))
                value = Decimal(result.values[-1][1])
            except (ValueError, InvalidOperation):
                continue
            if session_id not in requested_session_ids or not value.is_finite():
                continue
            if session_id in values:
                raise InternalServerError(
                    f"Utilization query returned multiple values for session {session_id}"
                )
            values[session_id] = value
        return SessionUtilizationMetricResult(by_session=values)
