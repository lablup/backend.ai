from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import SessionAction
from ai.backend.manager.services.session.types import LegacySessionInfo


@dataclass
class GetSessionInfoAction(SessionAction):
    session_name: str
    owner_access_key: AccessKey

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_session_info"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetSessionInfoActionResult:
    session_info: LegacySessionInfo
    session_data: SessionData
