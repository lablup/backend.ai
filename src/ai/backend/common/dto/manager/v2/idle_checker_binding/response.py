from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.idle_checker_binding.types import IdleCheckerScopeTypeDTO
from ai.backend.common.identifier.idle_checker import IdleCheckerBindingID, IdleCheckerID


class IdleCheckerBindingNode(BaseResponseModel):
    id: IdleCheckerBindingID
    scope_type: IdleCheckerScopeTypeDTO
    scope_id: str
    idle_checker_id: IdleCheckerID
    enabled: bool
    created_at: datetime
    updated_at: datetime


class CreateIdleCheckerBindingPayload(BaseResponseModel):
    idle_checker_binding: IdleCheckerBindingNode


class UpdateIdleCheckerBindingPayload(BaseResponseModel):
    idle_checker_binding: IdleCheckerBindingNode


class PurgeIdleCheckerBindingPayload(BaseResponseModel):
    id: IdleCheckerBindingID


class SearchIdleCheckerBindingPayload(BaseResponseModel):
    items: list[IdleCheckerBindingNode] = Field(default_factory=list)
    total_count: int
    has_next_page: bool
    has_previous_page: bool
