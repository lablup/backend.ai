from __future__ import annotations

from ai.backend.common.types import BackendAISchema
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    MetricResultValue,
)
from ai.backend.manager.clients.prometheus.types import ValueType

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
