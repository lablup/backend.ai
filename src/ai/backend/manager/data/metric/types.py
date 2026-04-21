from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Self

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.types import KernelId

__all__ = [
    "DIFF_METRICS",
    "KernelLiveStatBatchResult",
    "KernelLiveStatEntry",
    "MetricValue",
    "RATE_METRICS",
    "UtilizationMetricType",
    "ValueType",
]


class UtilizationMetricType(enum.StrEnum):
    """Classification for how to wrap a PromQL query."""

    GAUGE = "gauge"
    RATE = "rate"
    DIFF = "diff"


# Metric-name -> UtilizationMetricType classification rules.
DIFF_METRICS: Final[frozenset[str]] = frozenset({"cpu_util"})
RATE_METRICS: Final[frozenset[str]] = frozenset({"net_rx", "net_tx"})


@dataclass(frozen=True)
class KernelLiveStatEntry:
    """All live_stat samples belonging to a single kernel.

    An empty `values` list represents "no Prometheus samples yet"
    """

    kernel_id: KernelId
    values: list[MetricValue]


@dataclass(frozen=True)
class KernelLiveStatBatchResult:
    # Per-kernel batch result for `query_kernel_live_stat_batch`

    entries: dict[KernelId, KernelLiveStatEntry]

    @classmethod
    def empty(cls, kernel_ids: Sequence[KernelId]) -> Self:
        return cls.from_metric_values(kernel_ids, {})

    @classmethod
    def from_metric_values(
        cls,
        kernel_ids: Sequence[KernelId],
        values_by_kernel: Mapping[KernelId, Sequence[MetricValue]],
    ) -> Self:
        return cls(
            entries={
                kid: KernelLiveStatEntry(
                    kernel_id=kid,
                    values=list(values_by_kernel.get(kid, [])),
                )
                for kid in kernel_ids
            }
        )
