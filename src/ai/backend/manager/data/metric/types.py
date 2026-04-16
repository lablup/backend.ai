from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Self

from ai.backend.common.types import KernelId


class ValueType(enum.StrEnum):
    """
    Specifies the type of a metric value.
    """

    CURRENT = "current"
    CAPACITY = "capacity"
    PCT = "pct"


@dataclass(frozen=True)
class KernelMetricValue:
    """A single (current|capacity) value for one metric of one kernel."""

    metric_name: str
    value_type: ValueType
    value: str


@dataclass(frozen=True)
class KernelLiveStatEntry:
    """All live_stat samples belonging to a single kernel.

    An empty ``values`` list represents "no Prometheus samples yet" --- callers
    do not need to handle ``None``; the entry is always present.
    """

    kernel_id: KernelId
    values: list[KernelMetricValue]


@dataclass(frozen=True)
class KernelLiveStatBatchResult:
    """Per-kernel batch result for ``query_kernel_live_stat_batch``.

    Always contains one entry per requested ``kernel_id``. Missing data is
    represented as an empty ``KernelLiveStatEntry.values`` list, never ``None``.
    """

    entries: dict[KernelId, KernelLiveStatEntry]

    @classmethod
    def empty(cls, kernel_ids: Sequence[KernelId]) -> Self:
        return cls.from_metric_values(kernel_ids, {})

    @classmethod
    def from_metric_values(
        cls,
        kernel_ids: Sequence[KernelId],
        values_by_kernel: Mapping[KernelId, Sequence[KernelMetricValue]],
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
