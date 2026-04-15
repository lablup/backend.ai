import asyncio
import logging
import re
from collections.abc import Sequence
from typing import Final
from uuid import UUID

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.dto.clients.prometheus.response import PrometheusResponse
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
    KernelLiveStatEntry,
    KernelMetricValue,
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
            return KernelLiveStatActionResult(stats=KernelLiveStatBatchResult(entries={}))
        try:
            gauge, diff, rate = await asyncio.gather(
                self._query_gauge_kernel_live_stat(action.kernel_ids),
                self._query_diff_kernel_live_stat(action.kernel_ids),
                self._query_rate_kernel_live_stat(action.kernel_ids),
            )
        except (PrometheusConnectionError, FailedToGetMetric):
            log.warning("Failed to query Prometheus for kernel live stats, returning empty results")
            return KernelLiveStatActionResult(
                stats=KernelLiveStatBatchResult(
                    entries={
                        kid: KernelLiveStatEntry(kernel_id=kid, values=[])
                        for kid in action.kernel_ids
                    }
                )
            )

        merged: dict[KernelId, list[KernelMetricValue]] = {}
        for partial in (gauge, diff, rate):
            for kid, values in partial.items():
                merged.setdefault(kid, []).extend(values)

        entries: dict[UUID, KernelLiveStatEntry] = {}
        for kid in action.kernel_ids:
            values = merged.get(kid, [])
            entries[kid] = KernelLiveStatEntry(kernel_id=kid, values=values)
        return KernelLiveStatActionResult(stats=KernelLiveStatBatchResult(entries=entries))

    async def _query_gauge_kernel_live_stat(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, list[KernelMetricValue]]:
        """Raw gauge values (both current + capacity) for metrics not derived via rate()."""
        preset = self._build_live_stat_preset(
            kernel_ids,
            metric_type=UtilizationMetricType.GAUGE,
        )
        response = await self._prometheus_client.query_instant(preset)
        return self._collect_metric_values(response)

    async def _query_diff_kernel_live_stat(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, list[KernelMetricValue]]:
        """cpu_util.current via rate() only (no division)."""
        preset = self._build_live_stat_preset(
            kernel_ids,
            metric_type=UtilizationMetricType.DIFF,
            metric_name_filter=DIFF_METRICS,
            value_type_filter=ValueType.CURRENT,
        )
        response = await self._prometheus_client.query_instant(preset)
        return self._collect_metric_values(response)

    async def _query_rate_kernel_live_stat(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, list[KernelMetricValue]]:
        """net_rx/net_tx.current via rate() / UTILIZATION_METRIC_INTERVAL."""
        preset = self._build_live_stat_preset(
            kernel_ids,
            metric_type=UtilizationMetricType.RATE,
            metric_name_filter=RATE_METRICS,
            value_type_filter=ValueType.CURRENT,
        )
        response = await self._prometheus_client.query_instant(preset)
        return self._collect_metric_values(response)

    def _collect_metric_values(
        self,
        response: PrometheusResponse,
    ) -> dict[KernelId, list[KernelMetricValue]]:
        """Parse a Prometheus response and group metric values by kernel_id."""
        result: dict[KernelId, list[KernelMetricValue]] = {}
        for metric_result in response.data.result:
            info = metric_result.metric
            if (
                info.kernel_id is None
                or info.container_metric_name is None
                or info.value_type is None
            ):
                continue
            if not metric_result.values:
                continue
            try:
                value_type = ValueType(info.value_type)
            except ValueError:
                continue
            _, raw_value = metric_result.values[-1]
            kid = KernelId(UUID(info.kernel_id))
            result.setdefault(kid, []).append(
                KernelMetricValue(
                    metric_name=info.container_metric_name,
                    value_type=value_type,
                    value=raw_value,
                )
            )
        return result

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
