"""Metric domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.dto.manager.v2.kernel.response import (
    KernelLiveStatInfo,
    KernelLiveStatMetricInfo,
)
from ai.backend.common.types import KernelId, MetricValue
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.clients.prometheus.live_stat_converter import LegacyLiveStatConverter
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
    def _metric_value_to_info(name: str, value: MetricValue) -> KernelLiveStatMetricInfo:
        return KernelLiveStatMetricInfo(
            metric_name=name,
            current=value["current"],
            capacity=value["capacity"],
            pct=value["pct"],
            unit_hint=value["unit_hint"],
            stats_max=value["stats.max"],
            stats_avg=value["stats.avg"],
            stats_rate=value["stats.rate"],
            stats_diff=value["stats.diff"],
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
        ids = [KernelId(kernel_id) for kernel_id in kernel_ids]
        converted = LegacyLiveStatConverter.convert(ids, action_result.stats)
        live_stats: list[KernelLiveStatInfo | None] = []
        for kernel_id in ids:
            metrics = converted.get(kernel_id)
            if metrics is None:
                live_stats.append(None)
                continue
            live_stats.append(
                KernelLiveStatInfo(
                    metrics=[
                        self._metric_value_to_info(name, value) for name, value in metrics.items()
                    ]
                )
            )
        return live_stats
