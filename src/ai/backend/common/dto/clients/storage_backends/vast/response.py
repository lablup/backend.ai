from __future__ import annotations

from pydantic import ConfigDict, Field

from ai.backend.common.dto.clients.storage_backends.vast.types import (
    VASTQuotaID,
)
from ai.backend.common.types import BackendAISchema


class VASTTokenPair(BackendAISchema):
    access_token: str
    refresh_token: str


class VASTPerformance(BackendAISchema):
    read_bw: int = -1
    read_iops: int = -1
    write_bw: float = -1
    write_iops: int = -1


class VASTClusterInfo(BackendAISchema):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    id: str
    guid: str
    ip: str
    mgmt_vip: str
    name: str
    state: str
    physical_space: int = -1
    physical_space_in_use: int = -1
    usable_capacity_bytes: int = -1
    iops: int = -1
    rd_iops: int = -1
    wr_iops: int = -1
    bw: int = -1
    rd_bw: int = -1
    wr_bw: int = -1
    latency: int = -1
    rd_latency: int = -1
    wr_latency: int = -1
    max_file_size: int = -1
    max_performance: VASTPerformance = Field(default_factory=VASTPerformance)


class VASTQuota(BackendAISchema):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    path: str
    id: VASTQuotaID
    guid: str
    name: str
    state: str
    grace_period: str
    soft_limit: int
    hard_limit: int
    soft_limit_inodes: int
    hard_limit_inodes: int
    used_inodes: int
    used_capacity: int
    percent_capacity: int


class VASTCapacityUsage(BackendAISchema):
    capacity_bytes: int
    used_bytes: int
