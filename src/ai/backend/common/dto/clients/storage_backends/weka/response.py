from __future__ import annotations

from pydantic import ConfigDict

from ai.backend.common.dto.clients.storage_backends.weka.types import (
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
