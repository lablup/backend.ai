from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerTypeDTO
from ai.backend.common.dto.manager.v2.prometheus_query_preset.types import MetricLabelEntryInfo
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.common.types import SessionTypes


class SessionLifetimeSpecInfo(BaseResponseModel):
    max_lifetime_seconds: int


class NetworkTimeoutSpecInfo(BaseResponseModel):
    max_network_inactivity_seconds: int


class UtilizationThresholdInfo(BaseResponseModel):
    preset_id: PrometheusQueryPresetID
    threshold: Decimal
    filter_labels: list[MetricLabelEntryInfo] = Field(
        description=f"Added in {NEXT_RELEASE_VERSION}. Label filters injected into the preset query."
    )
    group_labels: list[str] = Field(
        description=(
            f"Added in {NEXT_RELEASE_VERSION}. Group-by labels injected into the preset query."
        )
    )


class UtilizationSpecInfo(BaseResponseModel):
    max_underutilized_duration_seconds: int
    threshold: UtilizationThresholdInfo


class IdleCheckerSpecInfo(BaseResponseModel):
    type: IdleCheckerTypeDTO
    session_lifetime: SessionLifetimeSpecInfo | None = Field(default=None)
    network: NetworkTimeoutSpecInfo | None = Field(default=None)
    utilization: UtilizationSpecInfo | None = Field(default=None)


class IdleCheckerNode(BaseResponseModel):
    id: IdleCheckerID
    name: str
    description: str | None
    checker_type: IdleCheckerTypeDTO
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpecInfo
    created_at: datetime
    updated_at: datetime


class CreateIdleCheckerPayload(BaseResponseModel):
    idle_checker: IdleCheckerNode


class UpdateIdleCheckerPayload(BaseResponseModel):
    idle_checker: IdleCheckerNode


class PurgeIdleCheckerPayload(BaseResponseModel):
    id: IdleCheckerID


class SearchIdleCheckerPayload(BaseResponseModel):
    items: list[IdleCheckerNode] = Field(default_factory=list)
    total_count: int
    has_next_page: bool
    has_previous_page: bool
