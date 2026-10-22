from __future__ import annotations

from ai.backend.common.dto.clients.storage_backends.dellemc.response import (
    OneFSQuotaThresholds,
)
from ai.backend.common.dto.clients.storage_backends.dellemc.types import (
    OneFSQuotaType,
)
from ai.backend.common.types import BackendAISchema


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
