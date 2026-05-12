from __future__ import annotations

from ai.backend.common.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    MetricResultValue,
)
from ai.backend.common.clients.prometheus.types import ValueType
from ai.backend.common.types import BackendAISchema

__all__ = [
    "ContainerMetricOptionalLabel",
    "ContainerMetricResponseInfo",
    "ContainerMetricResult",
    "MetricQueryParameter",
    "MetricResultValue",
]


class MetricQueryParameter(BackendAISchema):
    metric_name: str
    value_type: ValueType
    start: str
    end: str
    step: str
