import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionAction


# TODO: Change this to BatchAction
@dataclass
class CheckAndTransitStatusAction(SessionAction):
    user_id: uuid.UUID
    user_role: UserRole
    session_ids: list[SessionId]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "check_and_transit_status_multi"


@dataclass
class CheckAndTransitStatusActionResult(BaseActionResult):
    # TODO: Add proper type
    session_status_map: dict[SessionId, str]

    @override
    def entity_id(self) -> Optional[str]:
        return None
