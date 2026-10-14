from __future__ import annotations

import enum
from typing import Any

from pydantic import ConfigDict, Field

from ai.backend.common.types import BackendAISchema


class OneFSQuotaType(enum.StrEnum):
    DIRECTORY = "directory"
    USER = "user"
    GROUP = "group"


class OneFSQuotaThresholds(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    hard: int | None = None
    soft: int | None = None


class OneFSMetadata(BackendAISchema):
    cluster: str
    nodes: str


class OneFSUsage(BackendAISchema):
    capacity_bytes: int
    used_bytes: int


class OneFSNodeHardware(BackendAISchema):
    id: int
    model: str
    configuration: str
    serial_number: str


class OneFSNodeStatus(BackendAISchema):
    batteries: list[dict[str, Any]]


class OneFSNodeMetadata(BackendAISchema):
    hardware: OneFSNodeHardware
    status: OneFSNodeStatus


class OneFSClusterConfig(BackendAISchema):
    name: str
    release: str
    build: str
    local_lnn: int


class OneFSNetworkInterface(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class OneFSClusterMetadata(BackendAISchema):
    config: OneFSClusterConfig
    interface: list[OneFSNetworkInterface]


class OneFSDriveStats(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class OneFSProtocolDiskStats(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    iops: float | None = None


class OneFSProtocolOneFSStats(BackendAISchema):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    in_: float | None = Field(default=None, alias="in")
    out: float | None = None


class OneFSProtocolStats(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    disk: OneFSProtocolDiskStats | None = None
    onefs: OneFSProtocolOneFSStats | None = None


class OneFSWorkloadStats(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    latency_read: float | None = None
    latency_write: float | None = None


class OneFSSystemStats(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class OneFSQuotaUsage(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    fslogical: int | None = None


class OneFSQuota(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    id: str
    thresholds: OneFSQuotaThresholds
    usage: OneFSQuotaUsage


class OneFSCreatedQuota(BackendAISchema):
    id: str


class OneFSCreateQuotaRequest(BackendAISchema):
    path: str
    type: OneFSQuotaType
    include_snapshots: bool = False
    thresholds: OneFSQuotaThresholds
    thresholds_on: str = "fslogicalsize"
    enforced: bool = True


class OneFSUpdateQuotaRequest(BackendAISchema):
    thresholds: OneFSQuotaThresholds


class OneFSWorkloadStatsQuery(BackendAISchema):
    system_names: str | None = None
