import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.session.base import (
    SessionSingleEntityAction,
    SessionSingleEntityActionResult,
)
from ai.backend.manager.services.session.types import LegacySessionInfo


@dataclass
class GetSessionInfoAction(SessionSingleEntityAction):
    session_id: uuid.UUID
    owner_access_key: AccessKey

    @override
    def target_entity_id(self) -> str:
        return str(self.session_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.SESSION, str(self.session_id))

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetSessionInfoActionResult(SessionSingleEntityActionResult):
    session_info: LegacySessionInfo
    session_data: SessionData

    @override
    def target_entity_id(self) -> str:
        return str(self.session_data.id)
