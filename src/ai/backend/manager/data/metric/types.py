from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from ai.backend.common.types import KernelAggregationMode, SessionId


@dataclass(frozen=True)
class SessionUtilizationMetricThreshold:
    metric_name: str
    time_window_seconds: int | None
    threshold: Decimal
    kernel_aggregation: KernelAggregationMode


@dataclass(frozen=True)
class SessionUtilizationMetricResult:
    by_session: Mapping[SessionId, Decimal]
