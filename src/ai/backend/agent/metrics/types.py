import uuid
from dataclasses import dataclass
from typing import (
    NewType,
    Optional,
)

from ai.backend.common.types import (
    PID,
    AgentId,
    ContainerId,
    DeviceId,
    KernelId,
    MetricKey,
    SessionId,
)

MetricValueFieldKey = NewType("MetricValueFieldKey", str)
MetricValueFieldPair = tuple[MetricValueFieldKey, str]

CURRENT_METRIC_KEY = MetricValueFieldKey("current")
CAPACITY_METRIC_KEY = MetricValueFieldKey("capacity")
PCT_METRIC_KEY = MetricValueFieldKey("pct")
ALL_METRIC_VALUE_TYPES = {CURRENT_METRIC_KEY, CAPACITY_METRIC_KEY, PCT_METRIC_KEY}


@dataclass
class FlattenedKernelMetric:
    agent_id: AgentId
    kernel_id: KernelId
    session_id: Optional[SessionId]
    owner_user_id: Optional[uuid.UUID]
    project_id: Optional[uuid.UUID]
    key: MetricKey
    value_pairs: list[MetricValueFieldPair]


@dataclass
class FlattenedDeviceMetric:
    agent_id: AgentId
    device_id: DeviceId
    key: MetricKey
    value_pairs: list[MetricValueFieldPair]


@dataclass
class FlattenedProcessMetric:
    agent_id: AgentId
    kernel_id: KernelId
    session_id: SessionId | None
    owner_user_id: uuid.UUID | None
    project_id: uuid.UUID | None
    container_id: ContainerId
    pid: PID
    key: MetricKey
    value_pairs: list[MetricValueFieldPair]
