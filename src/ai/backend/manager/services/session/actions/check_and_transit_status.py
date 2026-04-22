from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction

if TYPE_CHECKING:
    from ai.backend.manager.models.user import UserRole


@dataclass
class CheckAndTransitStatusAction(SessionAction):
    user_id: uuid.UUID
    user_role: UserRole
    session_id: SessionId

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class CheckAndTransitStatusActionResult(BaseActionResult):
    # TODO: Add proper type
    result: dict[SessionId, str]
    session_data: SessionData

    @override
    def entity_id(self) -> str | None:
        return str(self.session_data.id)
