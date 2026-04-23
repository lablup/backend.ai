import asyncio
import logging
import re
from collections.abc import Sequence
from typing import Final

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.clients.prometheus.querier import ContainerMetricQuerier
from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.exception import (
    BackendAIError,
    FailedToGetMetric,
    PrometheusConnectionError,
    UnreachableError,
)
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    CONTAINER_UTILIZATION_METRIC_NAME,
    UTILIZATION_METRIC_INTERVAL,
)
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.metric.types import (
    DIFF_METRICS,
    RATE_METRICS,
    KernelLiveStatBatchResult,
    MetricType,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.metric.types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    KernelMetricValuesByKernel,
    MetricResultValue,
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

_LIVE_STAT_GROUP_BY: Final[frozenset[str]] = frozenset({
    "kernel_id",
    "container_metric_name",
    "value_type",
})

_GAUGE_TEMPLATE: Final[str] = (
    f"sum by ({{group_by}})({CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}})"
)
_RATE_TEMPLATE: Final[str] = (
    "sum by ({group_by})(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
    f" / {UTILIZATION_METRIC_INTERVAL}"
)
_DIFF_TEMPLATE: Final[str] = (
    "sum by ({group_by})(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
)


def _regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value) for value in values)


class MetricRepository:
    _db: ExtendedAsyncSAEngine
    _prometheus_client: PrometheusClient
    _timewindow: str

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        prometheus_client: PrometheusClient,
        timewindow: str,
    ) -> None:
        self._db = db
        self._prometheus_client = prometheus_client
        self._timewindow = timewindow

    async def query_container_metric_metadata(self) -> list[str]:
        result = await self._prometheus_client.query_label_values(
            label_name=CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
            metric_match=CONTAINER_UTILIZATION_METRIC_NAME,
        )
        return result.data

    async def query_container_metric(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
        time_range: QueryTimeRange,
    ) -> list[ContainerMetricResult]:
        preset = self._build_container_metric_preset(metric_name, label)
        response = await self._prometheus_client.query_range(preset, time_range)
        return [
            ContainerMetricResult(
                metric=ContainerMetricResponseInfo.from_metric_response_info(m.metric),
                values=[MetricResultValue(*value) for value in m.values],
            )
            for m in response.data.result
        ]

    async def query_kernel_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> KernelLiveStatBatchResult:
        """Query Prometheus for live stats of the given kernels.

        Issues three concurrent queries (gauge/diff/rate) and merges results.
        Returns a KernelLiveStatBatchResult with per-kernel entries.
        """
        if not kernel_ids:
            return KernelLiveStatBatchResult.empty(kernel_ids)
        try:
            values_by_kernel = await self._query_kernel_live_stats(kernel_ids)
        except (PrometheusConnectionError, FailedToGetMetric):
            log.warning("Failed to query Prometheus for kernel live stats, returning empty results")
            return KernelLiveStatBatchResult.empty(kernel_ids)
        return KernelLiveStatBatchResult.from_metric_values(kernel_ids, values_by_kernel)

    async def _query_kernel_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, list[MetricValue]]:
        gauge, diff, rate = await asyncio.gather(
            self._query_kernel_live_stat(
                kernel_ids,
                metric_type=MetricType.GAUGE,
            ),
            self._query_kernel_live_stat(
                kernel_ids,
                metric_type=MetricType.DIFF,
                metric_name_filter=DIFF_METRICS,
                value_type_filter=ValueType.CURRENT,
            ),
            self._query_kernel_live_stat(
                kernel_ids,
                metric_type=MetricType.RATE,
                metric_name_filter=RATE_METRICS,
                value_type_filter=ValueType.CURRENT,
            ),
        )
        merged = gauge.merged_with(diff).merged_with(rate)
        return merged.values_by_kernel

    async def _query_kernel_live_stat(
        self,
        kernel_ids: Sequence[KernelId],
        *,
        metric_type: MetricType,
        metric_name_filter: frozenset[str] | None = None,
        value_type_filter: ValueType | None = None,
    ) -> KernelMetricValuesByKernel:
        preset = self._build_live_stat_preset(
            kernel_ids,
            metric_type=metric_type,
            metric_name_filter=metric_name_filter,
            value_type_filter=value_type_filter,
        )
        response = await self._prometheus_client.query_instant(preset)
        return KernelMetricValuesByKernel.from_prometheus_response(response)

    def _get_metric_type(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> MetricType:
        # TODO: Refactor to query metric metadata from DB Source
        #       once the metadata persistence is available.
        if metric_name in DIFF_METRICS and label.value_type == ValueType.CURRENT:
            return MetricType.DIFF
        if metric_name in RATE_METRICS:
            return MetricType.RATE
        return MetricType.GAUGE

    def _build_container_metric_preset(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> MetricPreset:
        metric_type = self._get_metric_type(metric_name, label)
        querier = ContainerMetricQuerier(
            metric_name=metric_name,
            value_type=ValueType(label.value_type.value),
            kernel_id=label.kernel_id,
            session_id=label.session_id,
            agent_id=label.agent_id,
            user_id=label.user_id,
            project_id=label.project_id,
        )
        match metric_type:
            # TODO: Define device metadata for each metric
            # TODO: Refactor metric template retrieval to query metric metadata from DB Source
            case MetricType.GAUGE:
                template = (
                    "sum by ({group_by})(" + CONTAINER_UTILIZATION_METRIC_NAME + "{{{labels}}})"
                )
            case MetricType.RATE:
                template = (
                    "sum by ({group_by})(rate("
                    + CONTAINER_UTILIZATION_METRIC_NAME
                    + "{{{labels}}}[{window}]))"
                    " / " + str(UTILIZATION_METRIC_INTERVAL)
                )
            case MetricType.DIFF:
                template = (
                    "sum by ({group_by})(rate("
                    + CONTAINER_UTILIZATION_METRIC_NAME
                    + "{{{labels}}}[{window}]))"
                )
            case _:
                raise UnreachableError(f"Unknown metric type: {metric_type}")
        return MetricPreset(
            template=template,
            labels=querier.labels(),
            group_by=querier.group_by_labels(),
            window=self._timewindow,
        )

    def _build_live_stat_preset(
        self,
        kernel_ids: Sequence[KernelId],
        *,
        metric_type: MetricType,
        metric_name_filter: frozenset[str] | None = None,
        value_type_filter: ValueType | None = None,
    ) -> MetricPreset:
        labels: dict[str, LabelMatcher] = {
            "kernel_id": LabelMatcher.regex(_regex_union([str(kid) for kid in kernel_ids]))
        }
        if metric_name_filter is not None:
            labels["container_metric_name"] = LabelMatcher.regex(
                _regex_union(sorted(metric_name_filter))
            )
        if value_type_filter is not None:
            labels["value_type"] = LabelMatcher.exact(value_type_filter.value)

        match metric_type:
            case MetricType.GAUGE:
                template = _GAUGE_TEMPLATE
            case MetricType.RATE:
                template = _RATE_TEMPLATE
            case MetricType.DIFF:
                template = _DIFF_TEMPLATE
            case _:
                raise UnreachableError(f"Unsupported metric type: {metric_type}")
        return MetricPreset(
            template=template,
            labels=labels,
            group_by=_LIVE_STAT_GROUP_BY,
            window=self._timewindow,
        )
