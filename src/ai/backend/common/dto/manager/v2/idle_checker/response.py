from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerTypeDTO
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionTypes


class SessionLifetimeSpecInfo(BaseResponseModel):
    max_lifetime_seconds: int


class IdleCheckerSpecInfo(BaseResponseModel):
    type: IdleCheckerTypeDTO
    session_lifetime: SessionLifetimeSpecInfo


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
