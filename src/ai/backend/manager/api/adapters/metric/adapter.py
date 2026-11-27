"""Metric domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.dto.manager.v2.kernel.response import (
    KernelLiveStatInfo,
    KernelLiveStatMetricInfo,
)
from ai.backend.common.metrics.types import CAPACITY_SENTINEL, CAPACITY_SENTINEL_METRICS
from ai.backend.common.types import KernelId
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.clients.prometheus.metric_types import (
    DIFF_METRICS,
    RATE_METRICS,
    KernelLiveStatValues,
    resolve_container_metric_unit_hint,
)
from ai.backend.manager.services.metric.actions.batch_get_kernel_live_stats import (
    BatchGetKernelLiveStatsAction,
)
from ai.backend.manager.services.metric.processors import MetricProcessors


class MetricAdapter(BaseAdapter):
    """Adapter for the metrics read from the metric store."""

    _metric: MetricProcessors

    def __init__(self, metric: MetricProcessors) -> None:
        self._metric = metric

    @staticmethod
    def _metric_to_info(values: KernelLiveStatValues, name: str) -> KernelLiveStatMetricInfo:
        # The rate queries answer only the counter metrics, whose rate is the meaningful value.
        current = values.rate_current.get(name) or values.instant_current.get(name)
        capacity = values.instant_capacity.get(name)
        if current is not None and name in CAPACITY_SENTINEL_METRICS:
            capacity = CAPACITY_SENTINEL
        pct = "0"
        try:
            if current is not None and capacity is not None and Decimal(capacity) > 0:
                pct = f"{Decimal(current) / Decimal(capacity) * 100:.2f}"
        except InvalidOperation:
            pass
        return KernelLiveStatMetricInfo(
            metric_name=name,
            current=current or "0",
            capacity=capacity or "0",
            pct=pct,
            unit_hint=resolve_container_metric_unit_hint(name),
            stats_max=values.rate_max.get(name) or values.max.get(name) or "0",
            stats_avg=values.rate_avg.get(name) or values.avg.get(name) or "0",
            stats_rate=(current or "0") if name in RATE_METRICS else "0",
            stats_diff=(current or "0") if name in DIFF_METRICS else "0",
        )

    async def batch_get_kernel_live_stats(
        self, kernel_ids: Sequence[KernelID]
    ) -> list[KernelLiveStatInfo | None]:
        """The live statistics of each kernel, in the order of the ids.

        A kernel the metric store has no sample of answers None.
        """
        if not kernel_ids:
            return []
        action_result = await self._metric.batch_get_kernel_live_stats.run(
            BatchGetKernelLiveStatsAction(kernel_ids=list(kernel_ids))
        )
        live_stats: list[KernelLiveStatInfo | None] = []
        for kernel_id in kernel_ids:
            values = action_result.stats.by_kernel.get(KernelId(kernel_id))
            metric_names = (
                values.instant_current.keys()
                | values.instant_capacity.keys()
                | values.rate_current.keys()
                | values.max.keys()
                | values.rate_max.keys()
                | values.avg.keys()
                | values.rate_avg.keys()
                if values is not None
                else set()
            )
            if values is None or not metric_names:
                live_stats.append(None)
                continue
            live_stats.append(
                KernelLiveStatInfo(
                    metrics=[self._metric_to_info(values, name) for name in sorted(metric_names)]
                )
            )
        return live_stats
