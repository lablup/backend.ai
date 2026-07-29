from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID, IdleCheckerID


class IdleCheckerAssignmentNode(BaseResponseModel):
    id: IdleCheckerAssignmentID
    scope_type: IdleCheckerScopeTypeDTO
    scope_id: UUID
    idle_checker_id: IdleCheckerID
    enabled: bool
    created_at: datetime
    updated_at: datetime


class CreateIdleCheckerAssignmentPayload(BaseResponseModel):
    idle_checker_assignment: IdleCheckerAssignmentNode


class UpdateIdleCheckerAssignmentPayload(BaseResponseModel):
    idle_checker_assignment: IdleCheckerAssignmentNode


class PurgeIdleCheckerAssignmentPayload(BaseResponseModel):
    id: IdleCheckerAssignmentID


class SearchIdleCheckerAssignmentPayload(BaseResponseModel):
    items: list[IdleCheckerAssignmentNode] = Field(default_factory=list)
    total_count: int
    has_next_page: bool
    has_previous_page: bool
