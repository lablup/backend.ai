import asyncio
import logging
import re
from collections.abc import Sequence
from typing import Final

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.metrics.types import (
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
    UtilizationMetricType,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.metric.types import KernelMetricValuesByKernel

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

    async def query_kernel_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> dict[KernelId, list[MetricValue]]:
        """Query Prometheus for live stats of the given kernels.

        Issues three concurrent queries (gauge/diff/rate) and merges results.
        Returns a mapping of kernel_id -> list of metric values.
        """
        gauge, diff, rate = await asyncio.gather(
            self._query_kernel_live_stat(
                kernel_ids,
                metric_type=UtilizationMetricType.GAUGE,
            ),
            self._query_kernel_live_stat(
                kernel_ids,
                metric_type=UtilizationMetricType.DIFF,
                metric_name_filter=DIFF_METRICS,
                value_type_filter=ValueType.CURRENT,
            ),
            self._query_kernel_live_stat(
                kernel_ids,
                metric_type=UtilizationMetricType.RATE,
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
        metric_type: str,
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
        metric_type: str,
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
            case UtilizationMetricType.GAUGE:
                template = (
                    f"sum by ({{group_by}})({CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}})"
                )
            case UtilizationMetricType.RATE:
                template = (
                    "sum by ({group_by})(rate("
                    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
                    f" / {UTILIZATION_METRIC_INTERVAL}"
                )
            case UtilizationMetricType.DIFF:
                template = (
                    "sum by ({group_by})(rate("
                    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
                )
            case _:
                template = (
                    f"sum by ({{group_by}})({CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}})"
                )
        return MetricPreset(
            template=template,
            labels=labels,
            group_by=_LIVE_STAT_GROUP_BY,
            window=self._timewindow,
        )
