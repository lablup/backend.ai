from dataclasses import dataclass
from typing import (
    NewType,
)

from ai.backend.common.types import AgentId, DeviceId, KernelId, MetricKey

MetricValueFieldKey = NewType("MetricValueFieldKey", str)
MetricValueFieldPair = tuple[MetricValueFieldKey, str]

CURRENT_METRIC_KEY = MetricValueFieldKey("current")
CAPACITY_METRIC_KEY = MetricValueFieldKey("capacity")
PCT_METRIC_KEY = MetricValueFieldKey("pct")


@dataclass
class FlattenedKernelMetric:
    agent_id: AgentId
    kernel_id: KernelId
    key: MetricKey
    value_pairs: list[MetricValueFieldPair]


@dataclass
class FlattenedDeviceMetric:
    agent_id: AgentId
    device_id: DeviceId
    key: MetricKey
    value_pairs: list[MetricValueFieldPair]
