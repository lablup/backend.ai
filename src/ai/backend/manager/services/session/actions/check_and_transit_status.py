import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import SessionId
from ai.backend.manager.actions.action import BaseActionResult, BaseBatchActionResult
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.services.session.base import SessionAction, SessionBatchAction


@dataclass
class CheckAndTransitStatusAction(SessionAction):
    user_id: uuid.UUID
    user_role: UserRole
    session_id: SessionId

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "check_and_transit_status"


@dataclass
class CheckAndTransitStatusActionResult(BaseActionResult):
    # TODO: Add proper type
    result: dict[SessionId, str]
    session_data: SessionData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.session_data.id)


# TODO: Change this to BatchAction
@dataclass
class CheckAndTransitStatusBatchAction(SessionBatchAction):
    user_id: uuid.UUID
    user_role: UserRole
    session_ids: list[SessionId]

    @override
    def entity_ids(self) -> list[str]:
        return [str(session_id) for session_id in self.session_ids]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "check_and_transit_status_multi"


@dataclass
class CheckAndTransitStatusBatchActionResult(BaseBatchActionResult):
    # TODO: Add proper type
    session_status_map: dict[SessionId, str]

    @override
    def entity_ids(self) -> list[str]:
        return [str(session_id) for session_id in self.session_status_map.keys()]
