import logging
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from ai.backend.common.data.idle_checker.types import SESSION_ID_LABEL
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
from ai.backend.manager.clients.prometheus.preset import LabelMatcher, MetricPreset, regex_union
from ai.backend.manager.data.idle_checker.types import SessionUtilizationQuery
from ai.backend.manager.data.prometheus_query_preset import PrometheusQueryPresetData
from ai.backend.manager.models.prometheus_query_preset.conditions import (
    PrometheusQueryPresetConditions,
)
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
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
    _default_timewindow: str

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        prometheus_client: PrometheusClient,
        default_timewindow: str,
    ) -> None:
        self._prometheus_client = prometheus_client
        self._prometheus_query_preset_db_source = PrometheusQueryPresetDBSource(db)
        self._default_timewindow = default_timewindow

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
        session_ids_by_query: Mapping[
            SessionUtilizationQuery,
            Sequence[SessionId],
        ],
        evaluation_time: datetime,
    ) -> Mapping[SessionUtilizationQuery, Mapping[SessionId, Decimal]]:
        queries = {
            query: session_ids for query, session_ids in session_ids_by_query.items() if session_ids
        }
        if not queries:
            return {}
        preset_result = await self._prometheus_query_preset_db_source.search(
            BatchQuerier(
                pagination=NoPagination(),
                conditions=[
                    PrometheusQueryPresetConditions.by_ids(
                        list({query.preset_id for query in queries})
                    )
                ],
            )
        )
        presets_by_id = {
            PrometheusQueryPresetID(preset.id): preset for preset in preset_result.items
        }

        values_by_query: dict[
            SessionUtilizationQuery,
            Mapping[SessionId, Decimal],
        ] = {}
        for query, session_ids in queries.items():
            preset = presets_by_id.get(query.preset_id)
            if preset is None:
                log.error(
                    "Prometheus query preset not found; skipping utilization query: ID - {}",
                    query.preset_id,
                )
                values_by_query[query] = {}
                continue
            values_by_query[query] = await self._query_session_utilization_metrics_for_preset(
                preset,
                query,
                session_ids,
                evaluation_time,
            )
        return values_by_query

    def _invalid_labels(
        self,
        preset: PrometheusQueryPresetData,
        query: SessionUtilizationQuery,
    ) -> set[str]:
        """Spec labels the preset does not declare as allowed (empty allow-list allows all)."""
        invalid: set[str] = set()
        if preset.filter_labels:
            invalid |= {name for name, _ in query.filter_labels} - set(preset.filter_labels)
        if preset.group_labels:
            invalid |= set(query.group_labels) - set(preset.group_labels)
        return invalid

    async def _query_session_utilization_metrics_for_preset(
        self,
        preset: PrometheusQueryPresetData,
        query: SessionUtilizationQuery,
        session_ids: Sequence[SessionId],
        evaluation_time: datetime,
    ) -> Mapping[SessionId, Decimal]:
        invalid_labels = self._invalid_labels(preset, query)
        if invalid_labels:
            log.error(
                "Utilization query labels not allowed by preset {}; skipping: {}",
                preset.id,
                sorted(invalid_labels),
            )
            return {}
        filter_labels: dict[str, LabelMatcher] = {
            name: LabelMatcher.exact(value) for name, value in query.filter_labels
        }
        # Scope to the current session batch unless the user set session_id themselves.
        if SESSION_ID_LABEL in query.group_labels and SESSION_ID_LABEL not in filter_labels:
            filter_labels[SESSION_ID_LABEL] = LabelMatcher.regex(
                # remove duplicates while preserving order, then join into a regex union
                regex_union([str(session_id) for session_id in dict.fromkeys(session_ids)])
            )
        try:
            response = await self._prometheus_client.execute_preset(
                MetricPreset(
                    template=preset.query_template,
                    labels=filter_labels,
                    group_by=set(query.group_labels),
                    window=preset.time_window or self._default_timewindow,
                ),
                time_range=None,
                time=evaluation_time.isoformat(),
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
            # Extra group labels may yield multiple series per session;
            # a session is active if any of its series is active, hence max.
            existing = values.get(session_id)
            values[session_id] = value if existing is None else max(existing, value)
        if not values and response.data.result:
            log.warning(
                "Utilization query for preset {} returned {} series but none matched the "
                "requested sessions; check that group_labels include 'session_id'",
                preset.id,
                len(response.data.result),
            )
        return values
