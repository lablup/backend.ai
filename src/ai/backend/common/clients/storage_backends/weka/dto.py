from __future__ import annotations

import time

from pydantic import ConfigDict, Field

from ai.backend.common.clients.storage_backends.weka.types import (
    WekaQuotaID,
)
from ai.backend.common.types import BackendAISchema


class WekaQuota(BackendAISchema):
    quota_id: WekaQuotaID
    inode_id: int
    hard_limit: int | None
    soft_limit: int | None
    grace_seconds: int | None
    used_bytes: int | None


class WekaFs(BackendAISchema):
    id: str
    name: str
    uid: str
    group_id: str
    group_name: str
    used_total_data: int
    used_total: int
    free_total: int
    available_total: int
    available_ssd_metadata: int
    used_ssd: int
    free_ssd: int
    available_ssd: int
    ssd_budget: int
    total_budget: int


class WekaHealthCheck(BackendAISchema):
    """Raw text body of ``/healthcheck``."""

    status: str


class WekaClusterInfo(BackendAISchema):
    model_config = ConfigDict(extra="allow")


class WekaStatsEntry(BackendAISchema):
    model_config = ConfigDict(extra="allow")

    stats: dict[str, float | None]


class WekaMetrics(BackendAISchema):
    """Stats entries keyed by category, from the ``all`` group of ``/stats``."""

    categories: dict[str, list[WekaStatsEntry]]


class WekaLoginRequest(BackendAISchema):
    username: str
    password: str
    org: str


class WekaRefreshLoginRequest(BackendAISchema):
    refresh_token: str


class WekaSetQuotaRequest(BackendAISchema):
    grace_seconds: int | None = None
    soft_limit_bytes: str
    hard_limit_bytes: str


class WekaSetQuotaV1Params(BackendAISchema):
    activate: bool = True
    inode_context: int
    path: str
    soft_limit_bytes: int | None = None
    hard_limit_bytes: int | None = None


class WekaSetQuotaV1Request(BackendAISchema):
    """JSON-RPC body of the V1 ``set_directory_quota`` call."""

    id: float = Field(default_factory=lambda: time.time() * 1000)
    jsonrpc: str = "2.0"
    method: str = "set_directory_quota"
    params: WekaSetQuotaV1Params


class WekaGetMetricQuery(BackendAISchema):
    start_time: str
    end_time: str | None = None
    category: str | None = None
    stat: list[str]
