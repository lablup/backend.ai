import asyncio
import logging
import re
from collections.abc import Sequence
from typing import Final

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.exception import (
    FailedToGetMetric,
    PrometheusConnectionError,
    UnreachableError,
)
from ai.backend.common.metrics.types import UTILIZATION_METRIC_INTERVAL
from ai.backend.common.types import KernelId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.metric.repository import MetricRepository

from .actions.live_stat import KernelLiveStatAction, KernelLiveStatActionResult
from .container_metric import (
    CONTAINER_UTILIZATION_METRIC_NAME,
    ContainerUtilizationMetricService,
)
from .types import (
    DIFF_METRICS,
    RATE_METRICS,
    KernelLiveStatBatchResult,
    KernelMetricValuesByKernel,
    UtilizationMetricType,
    ValueType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_LIVE_STAT_GROUP_BY: Final[frozenset[str]] = frozenset({
    "kernel_id",
    "container_metric_name",
    "value_type",
})


def _regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value) for value in values)


class UtilizationMetricService:
    container: ContainerUtilizationMetricService
    _prometheus_client: PrometheusClient
    _timewindow: str
    _metric_repository: MetricRepository

    def __init__(
        self,
        prometheus_client: PrometheusClient,
        timewindow: str,
        metric_repository: MetricRepository,
    ) -> None:
        self._prometheus_client = prometheus_client
        self._timewindow = timewindow
        self.container = ContainerUtilizationMetricService(prometheus_client, timewindow=timewindow)
        self._metric_repository = metric_repository

    async def query_kernel_live_stat_batch(
        self,
        action: KernelLiveStatAction,
    ) -> KernelLiveStatActionResult:
        if not action.kernel_ids:
            return KernelLiveStatActionResult(
                stats=KernelLiveStatBatchResult.empty(action.kernel_ids)
            )
        try:
            gauge, diff, rate = await asyncio.gather(
                self._query_kernel_live_stat(
                    action.kernel_ids,
                    metric_type=UtilizationMetricType.GAUGE,
                ),
                self._query_kernel_live_stat(
                    action.kernel_ids,
                    metric_type=UtilizationMetricType.DIFF,
                    metric_name_filter=DIFF_METRICS,
                    value_type_filter=ValueType.CURRENT,
                ),
                self._query_kernel_live_stat(
                    action.kernel_ids,
                    metric_type=UtilizationMetricType.RATE,
                    metric_name_filter=RATE_METRICS,
                    value_type_filter=ValueType.CURRENT,
                ),
            )
        except (PrometheusConnectionError, FailedToGetMetric):
            log.warning("Failed to query Prometheus for kernel live stats, returning empty results")
            return KernelLiveStatActionResult(
                stats=KernelLiveStatBatchResult.empty(action.kernel_ids)
            )

        merged = gauge.merged_with(diff).merged_with(rate)
        return KernelLiveStatActionResult(
            stats=KernelLiveStatBatchResult.from_metric_values(
                action.kernel_ids,
                merged.values_by_kernel,
            )
        )

    async def _query_kernel_live_stat(
        self,
        kernel_ids: Sequence[KernelId],
        *,
        metric_type: UtilizationMetricType,
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

    def _build_live_stat_preset(
        self,
        kernel_ids: Sequence[KernelId],
        *,
        metric_type: UtilizationMetricType,
        metric_name_filter: frozenset[str] | None = None,
        value_type_filter: ValueType | None = None,
    ) -> MetricPreset:
        # TODO: Metrics repository should be used here to dynamically fetch metric names and label values instead of hardcoding regexes
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
            case UtilizationMetricType.GAUGE:
                template = (
                    "sum by ({group_by})(" + CONTAINER_UTILIZATION_METRIC_NAME + "{{{labels}}})"
                )
            case UtilizationMetricType.RATE:
                template = (
                    "sum by ({group_by})(rate("
                    + CONTAINER_UTILIZATION_METRIC_NAME
                    + "{{{labels}}}[{window}]))"
                    " / " + str(UTILIZATION_METRIC_INTERVAL)
                )
            case UtilizationMetricType.DIFF:
                template = (
                    "sum by ({group_by})(rate("
                    + CONTAINER_UTILIZATION_METRIC_NAME
                    + "{{{labels}}}[{window}]))"
                )
            case _:
                raise UnreachableError(f"Unsupported metric type: {metric_type}")
        return MetricPreset(
            template=template,
            labels=labels,
            group_by=_LIVE_STAT_GROUP_BY,
            window=self._timewindow,
        )
