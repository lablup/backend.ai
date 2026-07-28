import logging
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.exception import (
    BackendAIError,
    FailedToGetMetric,
    InvalidMetricPresetTemplate,
    PrometheusConnectionError,
)
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
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
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.models.prometheus_query_preset.conditions import (
    PrometheusQueryPresetConditions,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
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
        db: ExtendedAsyncSAEngine,
        prometheus_client: PrometheusClient,
    ) -> None:
        self._prometheus_client = prometheus_client
        self._prometheus_query_preset_db_source = PrometheusQueryPresetDBSource(db)

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
        session_ids_by_preset: Mapping[
            PrometheusQueryPresetID,
            Sequence[SessionId],
        ],
        evaluation_time: datetime,
    ) -> Mapping[PrometheusQueryPresetID, Mapping[SessionId, Decimal]]:
        preset_ids = [
            preset_id for preset_id, session_ids in session_ids_by_preset.items() if session_ids
        ]
        if not preset_ids:
            return {}
        preset_result = await self._prometheus_query_preset_db_source.search(
            BatchQuerier(
                pagination=NoPagination(),
                conditions=[PrometheusQueryPresetConditions.by_ids(preset_ids)],
            )
        )
        presets_by_id = {
            PrometheusQueryPresetID(preset.id): preset for preset in preset_result.items
        }

        values_by_preset: dict[
            PrometheusQueryPresetID,
            Mapping[SessionId, Decimal],
        ] = {}
        for preset_id in preset_ids:
            preset = presets_by_id.get(preset_id)
            if preset is None:
                log.error(
                    "Prometheus query preset not found; skipping utilization query: ID - {}",
                    preset_id,
                )
                values_by_preset[preset_id] = {}
                continue
            values_by_preset[preset_id] = await self._query_session_utilization_metrics_for_preset(
                preset,
                session_ids_by_preset[preset_id],
                evaluation_time,
            )
        return values_by_preset

    async def _query_session_utilization_metrics_for_preset(
        self,
        preset: PrometheusQueryPresetData,
        session_ids: Sequence[SessionId],
        evaluation_time: datetime,
    ) -> Mapping[SessionId, Decimal]:
        try:
            response = await self._prometheus_client.fetch_session_utilization(
                query_template=preset.query_template,
                time_window=preset.time_window or "",
                session_ids=session_ids,
                evaluation_time=evaluation_time.isoformat(),
            )
        except (PrometheusConnectionError, FailedToGetMetric, InvalidMetricPresetTemplate) as e:
            log.warning(
                "Utilization query failed for preset {}: {}",
                preset.id,
                e,
            )
            return {}
        requested_session_ids = set(session_ids)
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
        return values
