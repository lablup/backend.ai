from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Self

from ai.backend.common.clients.prometheus.types import MetricValue, ValueType
from ai.backend.common.types import KernelId

__all__ = [
    "DIFF_METRICS",
    "KernelLiveStatBatchResult",
    "KernelLiveStatEntry",
    "MetricValue",
    "RATE_METRICS",
    "MetricType",
    "ValueType",
]


class MetricType(StrEnum):
    """
    Specifies the type of a metric value.
    """

    GAUGE = "gauge"
    """
    Represents an instantly measured occupancy value.
    (e.g., used space as bytes, occupied amount as the number of items or a bandwidth)
    """
    RATE = "rate"
    """
    Represents a rate of changes calculated from underlying gauge/accumulation values
    (e.g., I/O bps calculated from RX/TX accum.bytes)
    """
    DIFF = "diff"
    """
    Represents a difference of changes calculated from underlying gauge/accumulation values
    (e.g., Utilization msec from CPU usage)
    """


# Metric-name -> MetricType classification rules.
# TODO: Refactor to query metric metadata from the repository layer once
#       the metadata persistence is available.
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
